#!/usr/bin/env -S uv run
# /// script
# requires-python = "==3.12.*"
# dependencies = ["matplotlib"]
# ///
"""Render benchmark scores by reasoning effort and cost as one interactive HTML page."""

import csv
import html
import io
import itertools
import json
import math
import re
from collections.abc import Iterator
from dataclasses import dataclass, field
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
    """A chart color replaced by its CSS variable in the generated SVG."""
    variable: str
    value: str


SURFACE = Color("surface", "#1a1a19")
PAGE = Color("page", "#0d0d0d")
TEXT_PRIMARY = Color("ink-1", "#ffffff")
TEXT_SECONDARY = Color("ink-2", "#c3c2b7")
TEXT_MUTED = Color("ink-3", "#898781")
GRIDLINE = Color("grid", "#2c2c2a")
BASELINE = Color("baseline", "#383835")
BORDER = Color("border", "rgba(255,255,255,0.10)")

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


GPT_6_ASTRA = Model("GPT-6 Astra", Color("series-2", "#d95926"))
GPT_6_2_ASTRA = Model("GPT-6.2 Astra", Color("series-8", "#f07770"))
CLAUDE_FABLE_5_2 = Model("Fable 5.2", Color("series-4", "#c98500"))
CLAUDE_OPUS_5_5 = Model("Opus 5.5", Color("series-5", "#d55181"))
GPT_6_1_SOL = Model("GPT-6.1 Sol", Color("series-6", "#008300"))
GPT_6_2_SOL = Model("GPT-6.2 Sol", Color("series-9", "#a5c93d"))
CLAUDE_SONNET_5_5 = Model("Sonnet 5.5", Color("series-7", "#9085e9"))
GEMINI_4_CARBON = Model("Gemini 4 Carbon", Color("series-1", "#2bb5a4"))
GEMINI_4_HYDROGEN = Model("Gemini 4 Hydrogen", Color("series-10", "#ba9d79"))
GEMINI_4_NEON = Model("Gemini 4 Neon", Color("series-11", "#6db7fa"))
MAI_CODE_2 = Model("MAI Code 2", Color("series-12", "#dc8ae0"))
MODELS = [GEMINI_4_NEON, MAI_CODE_2, GPT_6_ASTRA, GPT_6_2_ASTRA, GPT_6_1_SOL, GPT_6_2_SOL, CLAUDE_FABLE_5_2, CLAUDE_OPUS_5_5, CLAUDE_SONNET_5_5, GEMINI_4_CARBON, GEMINI_4_HYDROGEN]
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


CURVES = [
    Metric("AA Intelligence Index", "v5.0.1 · Artificial Analysis", {
        GEMINI_4_NEON: [44.1, 54.9, 59.6, 61.4, None],
        GPT_6_ASTRA: [43.3, 51.6, 54.8, 55.3, 56.9],
        GPT_6_1_SOL: [34.8, 46.3, 50.3, 52.5, 54.6],
        CLAUDE_FABLE_5_2: [53.9, 56.4, 61.8, 62.2, 64.6],
        CLAUDE_OPUS_5_5: [34.8, 48.2, 51.8, 57.4, 59.1],
        CLAUDE_SONNET_5_5: [25.6, 30.8, 41.5, 49.9, 54.5],
        GEMINI_4_CARBON: [54.2, 58.3, 60.0, None, None],
        GPT_6_2_ASTRA: [45.7, 57.0, 60.1, 61.6, 62.1],
        GPT_6_2_SOL: [40.6, 52.7, 54.9, 55.7, 57.3],
        GEMINI_4_HYDROGEN: [26.9, 41.2, 50.8, 53.9, None],
    }, (20, 70), 10),
    Metric("HLE-Diamond", "% · Humanity's Last Exam, AA's 1,000-question set · Artificial Analysis", {
        GEMINI_4_NEON: [54.2, 63.6, 68.4, 71.3, None],
        GPT_6_ASTRA: [45.1, 52.7, 59.3, 61.5, 63.8],
        GPT_6_1_SOL: [38.2, 46.0, 51.9, 55.8, 58.8],
        CLAUDE_FABLE_5_2: [60.8, 66.3, 73.8, 75.8, 80.2],
        CLAUDE_OPUS_5_5: [41.7, 51.4, 55.6, 64.0, 67.9],
        CLAUDE_SONNET_5_5: [20.6, 23.8, 33.8, 44.1, 53.3],
        GEMINI_4_CARBON: [61.9, 67.4, 69.1, None, None],
        GPT_6_2_ASTRA: [47.7, 56.0, 65.9, 67.3, 72.2],
        GPT_6_2_SOL: [34.5, 50.7, 58.3, 61.8, 64.0],
        GEMINI_4_HYDROGEN: [32.2, 47.7, 54.9, 58.8, None],
    }, (10, 90), 10),
    Metric("CritPt v2", "% · hard subset · Artificial Analysis", {
        GEMINI_4_NEON: [62.0, 61.5, 59.0, 60.5, None],
        GPT_6_ASTRA: [63.0, 72.0, 71.5, 71.0, 70.5],
        GPT_6_1_SOL: [62.5, 67.0, 68.5, 69.5, 69.5],
        CLAUDE_FABLE_5_2: [60.0, 61.5, 73.0, 73.5, 76.5],
        CLAUDE_OPUS_5_5: [36.0, 54.0, 59.5, 67.5, 68.0],
        CLAUDE_SONNET_5_5: [26.0, 33.5, 51.5, 57.5, 59.0],
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
        GEMINI_4_CARBON: [49.6, 94.2, 92.1, None, None],
        GPT_6_2_ASTRA: [91.7, 93.3, 94.6, 95.8, 95.8],
        GPT_6_2_SOL: [57.9, 82.9, 85.8, 85.8, 85.8],
    }, (20, 100), 20),
    Metric("AA-Omniscience Index", "v1.1 · −100 to 100 · Artificial Analysis", {
        GEMINI_4_NEON: [48.5, 51.1, 53.8, 54.8, None],
        GPT_6_ASTRA: [40.3, 41.4, 44.6, 43.7, 42.4],
        GPT_6_1_SOL: [38, 40.2, 41, 42.4, 42.0],
        CLAUDE_FABLE_5_2: [62.9, 63.5, 64.0, 64.8, 66.8],
        CLAUDE_OPUS_5_5: [39.0, 39.8, 42.4, 43.1, 48.1],
        CLAUDE_SONNET_5_5: [20.3, 18.6, 18.7, 20.6, 30.5],
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
        GEMINI_4_CARBON: [None, None, 1733, None, None],
    }, (1100, 1900), 200, decimals=0),
    Metric("AA-Briefcase", "Elo · long-horizon knowledge work · Artificial Analysis", {
        GEMINI_4_NEON: [1297.0, 1518.0, 1632.0, 1700.0, None],
        GPT_6_ASTRA: [1256, 1462, 1503, 1544, 1569],
        GPT_6_2_ASTRA: [1039, 1408, 1570, 1594, 1644],
        GPT_6_1_SOL: [1115, 1361, 1469, 1504, 1557],
        GPT_6_2_SOL: [1230, 1495, 1541, 1580, 1612],
        CLAUDE_FABLE_5_2: [1563, 1622, 1677, 1737, 1785],
        CLAUDE_OPUS_5_5: [1278, 1617, 1682, 1760, 1800],
        CLAUDE_SONNET_5_5: [1268, 1438, 1634, 1739, 1815],
        GEMINI_4_CARBON: [1567, 1602, 1611, None, None],
        GEMINI_4_HYDROGEN: [947, 1296, 1497, 1568, None],
    }, (800, 2000), 200, decimals=0),
    Metric("AutomationBench-AA", "% · Artificial Analysis", {
        GEMINI_4_NEON: [76.0, 77.8, 79.2, 79.3, None],
        GPT_6_ASTRA: [59.1, 64.6, 66.6, 67.2, 68.5],
        GPT_6_1_SOL: [52.6, 62.6, 64.5, 66.6, 64.9],
        CLAUDE_FABLE_5_2: [68.0, 68.8, 71.4, 74.2, 76.4],
        CLAUDE_OPUS_5_5: [52.9, 61.2, 63.2, 65.0, 69.5],
        CLAUDE_SONNET_5_5: [49.4, 54.9, 59.4, 65.5, 71.8],
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
        GEMINI_4_CARBON: [None, None, 79.3, None, None],
    }, (70, 90), 5),
    Metric("GDP.pdf", "% all-pass · Q&A over complex PDFs · Artificial Analysis", {
        GEMINI_4_NEON: [31.4, 32.8, 33.4, 28.0, None],
        GPT_6_ASTRA: [30.4, 30.4, 31.0, 32.2, 31.0],
        GPT_6_1_SOL: [27.0, 30.0, 32.0, 31.8, 31.0],
        CLAUDE_FABLE_5_2: [26.8, 23.8, 21.8, 21.4, 24.2],
        CLAUDE_OPUS_5_5: [25.6, 25.6, 28.8, 26.6, 26.2],
        CLAUDE_SONNET_5_5: [16.0, 20.2, 25.2, 24.6, 25.8],
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
    }, (30, 70), 10),
    Metric("Harvey LAB-AA v1.1", "% all-pass · Artificial Analysis; costs reported by OpenAI", {
        GPT_6_ASTRA: [None, None, None, None, 8.6],
        GPT_6_2_ASTRA: [2.2, 8.1, 13.3, 12.8, 15.0],
        GPT_6_1_SOL: [None, None, None, None, 6.9],
        GPT_6_2_SOL: [3.1, 5.0, 5.8, 6.1, 11.1],
        CLAUDE_FABLE_5_2: [4.2, 6.4, 4.7, 3.9, 7.2],
        CLAUDE_OPUS_5_5: [None, None, None, None, 4.2],
        CLAUDE_SONNET_5_5: [None, None, None, None, 2.8],
    }, (0, 20), 5),
    Metric("MLCR-AA", "% medical long-context reasoning · Artificial Analysis", {
        GPT_6_ASTRA: [33.9, 38.3, 32.8, 36.1, 41.7],
        GPT_6_2_ASTRA: [30.6, 32.8, 35.6, 37.8, 39.4],
        GPT_6_1_SOL: [26.7, 32.2, 31.7, 35.6, 38.3],
        GPT_6_2_SOL: [32.2, 31.7, 33.9, 35.0, 37.2],
        CLAUDE_FABLE_5_2: [None, None, None, None, 43.9],
        CLAUDE_OPUS_5_5: [19.4, 22.2, 15.0, 25.0, 27.8],
        CLAUDE_SONNET_5_5: [19.4, 17.8, 18.9, 20.6, 41.7],
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
        GEMINI_4_CARBON: [None, 89.2, None, None, None],
    }, (80, 95), 5),
    Metric("HealthBench Professional (AA)", "% length-adjusted score · Artificial Analysis", {
        GPT_6_ASTRA: [None, None, None, None, 66.0],
        GPT_6_1_SOL: [None, None, None, None, 65.1],
        CLAUDE_FABLE_5_2: [66.9, 67.0, 67.6, 68.1, 67.7],
        CLAUDE_OPUS_5_5: [None, None, None, None, 59.9],
        CLAUDE_SONNET_5_5: [None, None, None, None, 63.0],
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
    Metric("AA Index coding category", "FrontierCode-AA 2.0 at 15%, Terminal-Bench 4.0 at 10% · derived from AA", {
        GEMINI_4_NEON: [29.3, 44.0, 50.6, 52.1, None],
        GPT_6_ASTRA: [32.5, 41.7, 45.7, 48.7, 49.1],
        GPT_6_1_SOL: [24.4, 39.2, 42.6, 44.7, 46.8],
        CLAUDE_FABLE_5_2: [44.9, 46.8, 53.3, 53.2, 53.1],
        CLAUDE_OPUS_5_5: [22.0, 40.9, 44.2, 50.1, 51.7],
        CLAUDE_SONNET_5_5: [12.6, 18.5, 33.0, 44.2, 50.5],
        GEMINI_4_CARBON: [42.8, 47.9, 50.4, None, None],
        GPT_6_2_ASTRA: [40.0, 51.4, 52.3, 55.0, 52.9],
        GPT_6_2_SOL: [34.0, 47.3, 47.6, 48.1, 50.7],
        GEMINI_4_HYDROGEN: [8.2, 30.6, 43.4, 44.8, None],
    }, (0, 60), 10),
    Metric("Terminal-Bench 4.0", "% · Artificial Analysis", {
        GEMINI_4_NEON: [32.8, 54.5, 61.6, 63.6, None],
        GPT_6_ASTRA: [41.9, 49.5, 54.0, 59.6, 59.1],
        GPT_6_1_SOL: [30.8, 48.0, 51.5, 54.0, 56.1],
        CLAUDE_FABLE_5_2: [54.5, 55.1, 59.6, 61.6, 59.6],
        CLAUDE_OPUS_5_5: [31.3, 52.5, 56.6, 59.6, 59.6],
        CLAUDE_SONNET_5_5: [20.7, 29.8, 43.9, 57.1, 63.6],
        GEMINI_4_CARBON: [62.6, 60.6, 65.2, None, None],
        GPT_6_2_ASTRA: [51.0, 58.6, 60.1, 64.1, 64.1],
        GPT_6_2_SOL: [37.9, 56.1, 58.6, 56.1, 60.1],
        GEMINI_4_HYDROGEN: [6.6, 29.3, 54.0, 53.5, None],
    }, (0, 70), 10),
    Metric("FrontierCode-AA 2.0", "score · Cognition's tasks, AA's harness · Artificial Analysis", {
        GEMINI_4_NEON: [26.9, 36.9, 43.3, 44.4, None],
        GPT_6_ASTRA: [26.2, 36.6, 40.1, 41.4, 42.4],
        GPT_6_1_SOL: [20.2, 33.4, 36.7, 38.5, 40.6],
        CLAUDE_FABLE_5_2: [38.4, 41.3, 49.1, 47.6, 48.8],
        CLAUDE_OPUS_5_5: [15.8, 33.1, 35.9, 43.8, 46.4],
        CLAUDE_SONNET_5_5: [7.1, 11.0, 25.7, 35.6, 41.7],
        GEMINI_4_CARBON: [29.6, 39.5, 40.6, None, None],
        GPT_6_2_ASTRA: [32.7, 46.6, 47.1, 49.0, 45.4],
        GPT_6_2_SOL: [31.4, 41.4, 40.2, 42.8, 44.4],
        GEMINI_4_HYDROGEN: [9.3, 31.5, 36.3, 39.0, None],
    }, (0, 60), 10),
    Metric("Terminal-Bench Science 0.1", "% · Artificial Analysis", {
        GEMINI_4_NEON: [27.1, 54.8, 65.7, 70.0, None],
        GPT_6_ASTRA: [37.1, 53.3, 59.5, 54.8, 63.3],
        GPT_6_1_SOL: [11.0, 37.1, 46.2, 50.5, 58.1],
        CLAUDE_FABLE_5_2: [53.8, 60.5, 70.0, 67.6, 73.3],
        CLAUDE_OPUS_5_5: [24.3, 43.3, 49.0, 61.9, 59.0],
        CLAUDE_SONNET_5_5: [10.5, 16.2, 34.3, 52.4, 53.3],
        GEMINI_4_CARBON: [61.9, 62.4, 64.8, None, None],
        GPT_6_2_ASTRA: [51.0, 74.8, 75.2, 78.6, 78.1],
        GPT_6_2_SOL: [37.1, 60.5, 67.6, 66.7, 67.6],
        GEMINI_4_HYDROGEN: [2.4, 15.2, 41.4, 49.5, None],
    }, (0, 80), 10),
    Metric("DeepSWE v1.1", "% · each lab’s own harness; MAI: Copilot CLI 1.0.102", {
        MAI_CODE_2: [None, None, None, None, 73.2],
        GPT_6_ASTRA: [67.0, 72.8, 73.2, 74.1, 73.2],
        GPT_6_1_SOL: [64.4, 73.0, 75.2, 71.9, 71.9],
        CLAUDE_SONNET_5_5: [None, None, None, None, 71.0],
    }, (60, 80), 5),
    Metric('CursorBench 4.1', '% · Cursor leaderboard · updated tasks and agent time limit', {
        GEMINI_4_NEON: [45.5, 57.7, 63.7, 65.4, None],
        GEMINI_4_CARBON: [55.0, 60.4, 61.5, None, None],
        CLAUDE_FABLE_5_2: [53.4, 54.2, 56.5, 58.8, 61.3],
        CLAUDE_OPUS_5_5: [42.7, 50.0, 54.5, 56.7, 58.1],
        GEMINI_4_HYDROGEN: [23.9, 46.4, 57.3, 61.4, None],
        CLAUDE_SONNET_5_5: [31.8, 34.3, 43.8, 49.9, 54.4],
    }, (20, 70), 10, decimals=1),
    Metric("SciCode", "% · Artificial Analysis", {
        GPT_6_ASTRA: [54.1, 54.2, 55.4, 55.7, 56.5],
        GPT_6_1_SOL: [53.2, 53.2, 55.8, 55.7, 54.2],
        CLAUDE_FABLE_5_2: [57.8, 59.7, 59.5, 65.6, 67.7],
        CLAUDE_OPUS_5_5: [58.6, 59.3, 60.4, 65.0, 66.9],
        CLAUDE_SONNET_5_5: [49.1, 52.9, 53.7, 57.3, 61.0],
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
    Metric('MKA', '% weighted rubric score · Climb · Artificial Analysis', {
        GEMINI_4_NEON: [43.4, 50.9, 54.6, 56.5, None],
        CLAUDE_FABLE_5_2: [None, None, None, None, 56.6],
        GPT_6_2_ASTRA: [None, None, None, None, 52.7],
        GEMINI_4_CARBON: [None, None, 54.3, None, None],
        CLAUDE_OPUS_5_5: [None, None, None, None, 53.0],
        CLAUDE_SONNET_5_5: [None, None, None, None, 52.0],
        GPT_6_ASTRA: [None, None, None, None, 50.2],
        GPT_6_1_SOL: [None, None, None, None, 47.7],
    }, (35, 65), 5, decimals=1),
    Metric('Extended NYT Connections (940)', '% quadratic-v1 · one attempt, up to four trick words · Lech Mazur', {
        GEMINI_4_NEON: [None, None, 99.11, None, None],
        GEMINI_4_CARBON: [None, None, 99.3, None, None],
        GPT_6_ASTRA: [None, None, 97.73, 98.1, 98.4],
        GPT_6_2_ASTRA: [None, None, 98.23, None, None],
        GPT_6_1_SOL: [None, None, 95.49, None, 97.8],
        GPT_6_2_SOL: [None, None, 94.12, None, None],
        CLAUDE_FABLE_5_2: [None, None, 97.3, None, None],
        CLAUDE_OPUS_5_5: [None, 87.8, 88.5, None, None],
        CLAUDE_SONNET_5_5: [None, None, 80.5, None, None],
    }, (75, 100), 5, decimals=2),
    Metric('Extended NYT Connections (newest 100)', '% quadratic-v1 · one attempt, up to four trick words · Lech Mazur', {
        GEMINI_4_NEON: [None, None, 99.56, None, None],
        GEMINI_4_CARBON: [None, None, 99.56, None, None],
        GPT_6_ASTRA: [None, None, 97.81, 98.7, 97.9],
        GPT_6_2_ASTRA: [None, None, 98.25, None, None],
        GPT_6_1_SOL: [None, None, 95.63, None, 98.7],
        GPT_6_2_SOL: [None, None, 92.94, None, None],
        CLAUDE_FABLE_5_2: [None, None, 96.9, None, None],
        CLAUDE_OPUS_5_5: [None, 83.4, 90.6, None, None],
        CLAUDE_SONNET_5_5: [None, None, 79.1, None, None],
    }, (75, 100), 5, decimals=2),
    Metric('Vals Index (Vals reasoning study)', '% · Vals reasoning study · fixed ~half-task subset, not the full leaderboard', {
        GPT_6_ASTRA: [57.7, None, 62.4, None, 65.2],
        CLAUDE_OPUS_5_5: [55.9, None, 68.1, None, 69.6],
        GPT_6_2_ASTRA: [60.9, 63.9, 65.8, 67.3, 67.7],
        CLAUDE_FABLE_5_2: [None, None, 71.0, None, None],
    }, (0, 100), 20, decimals=1),
    Metric('EMB v1.1 (Vals reasoning study)', '% · Vals reasoning study · fixed ~half-task subset, not the full leaderboard', {
        GPT_6_ASTRA: [75.6, None, 75.2, None, 76.2],
        CLAUDE_OPUS_5_5: [75.3, None, 77.3, None, 78.6],
        GPT_6_2_ASTRA: [77.5, 78.4, 78.1, 79.4, 79.8],
        CLAUDE_FABLE_5_2: [77.1, None, 79.3, 79.6, 79.3],
    }, (0, 100), 20, decimals=1),
    Metric('Finance Agent v2.1 (Vals reasoning study)', '% · Vals reasoning study · fixed ~half-task subset, not the full leaderboard', {
        GPT_6_ASTRA: [54.9, None, 57.3, None, 57.6],
        CLAUDE_OPUS_5_5: [45.9, None, 60.8, None, 61.8],
        GPT_6_2_ASTRA: [55.0, 57.0, 56.0, 55.1, 56.3],
        CLAUDE_FABLE_5_2: [62.1, None, 63.7, 64.0, 63.6],
    }, (0, 100), 20, decimals=1),
    Metric('Legal Research Bench v1 (Vals reasoning study)', '% · Vals reasoning study · fixed ~half-task subset, not the full leaderboard', {
        GPT_6_ASTRA: [36.5, None, 38.5, None, 49.0],
        CLAUDE_OPUS_5_5: [27.9, None, 48.1, None, 55.8],
        GPT_6_2_ASTRA: [28.8, 37.5, 36.5, 46.2, 47.1],
        CLAUDE_FABLE_5_2: [44.2, None, 51.0, 50.0, None],
    }, (0, 100), 20, decimals=1),
    Metric('Tax Agent Bench v1 (Vals reasoning study)', '% · Vals reasoning study · fixed ~half-task subset, not the full leaderboard', {
        GPT_6_ASTRA: [20.8, None, 27.1, None, 26.0],
        CLAUDE_OPUS_5_5: [20.9, None, 31.2, None, 43.7],
        GPT_6_2_ASTRA: [13.1, 21.1, 24.3, 26.1, 25.2],
        CLAUDE_FABLE_5_2: [26.8, None, 35.4, 40.6, 39.6],
    }, (0, 100), 20, decimals=1),
    Metric('Vibe Code Bench v1.1 (Vals reasoning study)', '% · Vals reasoning study · fixed ~half-task subset, not the full leaderboard', {
        GPT_6_ASTRA: [83.5, None, 85.5, None, 91.1],
        CLAUDE_OPUS_5_5: [85.6, None, 92.3, None, 91.2],
        GPT_6_2_ASTRA: [79.6, 81.7, 91.4, 93.8, 93.6],
        CLAUDE_FABLE_5_2: [93.9, None, 94.9, None, None],
    }, (0, 100), 20, decimals=1),
    Metric('HLAB-Vals v1.1 (Vals reasoning study)', '% · Vals reasoning study · fixed ~half-task subset, not the full leaderboard', {
        GPT_6_ASTRA: [1.7, None, 5.0, None, 5.0],
        CLAUDE_OPUS_5_5: [5.0, None, 7.5, None, 7.5],
        GPT_6_2_ASTRA: [0.8, 10.0, 10.8, 16.7, 12.5],
        CLAUDE_FABLE_5_2: [4.2, None, 4.2, None, 0.0],
    }, (0, 100), 20, decimals=1),
    Metric('Terminal-Bench 4.0 (Vals) (Vals reasoning study)', '% · Vals reasoning study · fixed ~half-task subset, not the full leaderboard', {
        GPT_6_ASTRA: [44.4, None, 58.6, None, 56.6],
        CLAUDE_OPUS_5_5: [40.4, None, 67.7, None, 68.7],
        GPT_6_2_ASTRA: [49.5, 54.5, 61.6, 64.6, 61.6],
        CLAUDE_FABLE_5_2: [64.6, None, 71.7, 66.7, 59.6],
    }, (0, 100), 20, decimals=1),
    Metric('Terminal-Bench 4.1 (provider agents)', '% cheating-adjusted · public board; Neon: AA via Google, Antigravity CLI 1.5.9', {
        CLAUDE_OPUS_5_5: [None, None, None, None, 65.76],
        CLAUDE_FABLE_5_2: [None, None, None, None, 65.76],
        GEMINI_4_CARBON: [None, None, 64.55, None, None],
        CLAUDE_SONNET_5_5: [None, None, None, None, 63.94],
        GPT_6_2_ASTRA: [None, None, None, None, 62.12],
        GPT_6_2_SOL: [None, None, None, None, 61.52],
        GPT_6_1_SOL: [None, None, None, None, 60.91],
        GPT_6_ASTRA: [50.91, 55.15, 60.0, 59.7, 60.3],
        GEMINI_4_HYDROGEN: [None, None, 56.36, None, None],
        GEMINI_4_NEON: [None, None, None, 65.2, None],
    }, (45, 75), 20, decimals=2),
    Metric('FrontierCode 2.0 (Cognition)', '% weighted rubric aggregate · Cognition public provider-agent runs; not AA/OpenAI', {
        CLAUDE_FABLE_5_2: [35.26, 38.78, 46.24, 50.18, 48.23],
        GPT_6_ASTRA: [31.11, 37.29, 38.83, 41.69, 44.02],
        GPT_6_1_SOL: [25.74, 30.27, 35.09, 33.03, 39.65],
        GPT_6_2_ASTRA: [38.07, 42.2, 43.56, 44.12, 44.19],
        GPT_6_2_SOL: [33.14, 38.29, 39.72, 39.78, 43.76],
        GEMINI_4_CARBON: [31.53, 40.9, 42.62, None, None],
        GEMINI_4_HYDROGEN: [10.52, 28.21, 38.23, 38.87, None],
        GEMINI_4_NEON: [27.41, 38.16, 46.24, 44.83, None],
        CLAUDE_OPUS_5_5: [14.85, 31.43, 36.27, 44.72, 47.34],
        CLAUDE_SONNET_5_5: [9.66, 14.96, 22.95, 36.5, 42.24],
    }, (0, 60), 20, decimals=2),
    Metric('AutomationBench 1.0.6 (Zapier)', '% strict final-state task pass · Zapier API mode; provider-default fallbacks for Claude', {
        GEMINI_4_NEON: [49.62, 53.27, 54.34, 56.32, None],
        GEMINI_4_CARBON: [31.51, 52.97, 53.88, None, None],
        GPT_6_2_ASTRA: [37.14, 43.84, 47.95, 47.18, 52.36],
        CLAUDE_FABLE_5_2: [39.73, 40.18, 44.29, 47.95, 51.45],
        GEMINI_4_HYDROGEN: [30.59, 46.73, 51.14, None, None],
        CLAUDE_SONNET_5_5: [18.26, 23.29, 29.38, 36.83, 44.75],
        CLAUDE_OPUS_5_5: [24.2, 29.53, 33.03, 35.77, 42.47],
        GPT_6_ASTRA: [30.29, 34.09, 37.14, 38.96, 41.4],
        GPT_6_2_SOL: [31.2, 40.18, 41.25, 40.64, 41.1],
    }, (0, 65), 20, decimals=2),
    Metric("Agents' Last Exam v1.1 (public + Google)", '% partial-credit rubric score · public provider agents; Neon Google Antigravity CLI 1.4.8', {
        GPT_6_2_ASTRA: [65.77, 72.06, 75.96, 78.33, 77.61],
        GEMINI_4_CARBON: [None, None, 77.41, None, None],
        GPT_6_ASTRA: [67.87, 71.16, 71.04, 71.68, 73.14],
        GPT_6_2_SOL: [66.65, 70.26, 72.04, 72.48, 73.04],
        CLAUDE_FABLE_5_2: [None, None, None, None, 72.79],
        CLAUDE_OPUS_5_5: [None, None, None, None, 71.6],
        GEMINI_4_HYDROGEN: [51.68, 63.75, 68.89, 71.4, None],
        GEMINI_4_NEON: [None, None, None, 75.8, None],
    }, (40, 90), 20, decimals=2),
    Metric("CursorBench 4.0", "% · Cursor leaderboard; historical task set and time limit", {
        GEMINI_4_CARBON: [58.6, 60.1, 60.4, None, None],
        CLAUDE_FABLE_5_2: [53.2, 54.8, 56.9, 56.3, 60.0],
        CLAUDE_OPUS_5_5: [43.7, 52.5, 56.0, 56.0, 57.8],
        GEMINI_4_HYDROGEN: [27.9, 46.7, 54.3, 57.8, None],
        CLAUDE_SONNET_5_5: [35.8, 39.2, 47.8, 53.1, 55.5],
    }, (20, 70), 10),
    Metric("Terminal-Bench 2.1 (Microsoft)", "% · Microsoft Copilot CLI 1.0.102 · max · mean single attempt across three runs", {
        MAI_CODE_2: [None, None, None, None, 84.6],
        GPT_6_1_SOL: [None, None, None, None, 85.0],
        CLAUDE_OPUS_5_5: [None, None, None, None, 78.7],
    }, (75, 95), 5),
    Metric("FrontierCode-AA 1.1", "score · Artificial Analysis via Microsoft announcement", {
        MAI_CODE_2: [None, None, None, None, 52.0],
        GPT_6_1_SOL: [None, None, None, None, 49.4],
        CLAUDE_OPUS_5_5: [None, None, None, None, 56.0],
    }, (40, 60), 5),
    Metric("Terminal-Bench 2.1", "% · Artificial Analysis; historical run", {
        GPT_6_ASTRA: [88.0, 89.5, 89.9, 89.1, 88.4],
    }, (80, 95), 5),
    Metric("FrontierCode 1.1 Main", "score · Cognition leaderboard; historical run", {
        GPT_6_ASTRA: [45.3, 48.8, 50.9, 50.6, 53.3],
        GPT_6_1_SOL: [45.5, 50.2, 48.0, 49.3, 47.6],
        CLAUDE_OPUS_5_5: [47.3, 54.6, 54.0, 51.4, 54.4],
        CLAUDE_SONNET_5_5: [29.3, 36.5, 49.4, 52.1, 46.2],
    }, (20, 60), 10),
    Metric("Humanity's Last Exam", "% · full set · Artificial Analysis; historical run, not HLE-Diamond", {
        GPT_6_ASTRA: [49.2, 52.7, 53.1, 54.6, 54.7],
        GPT_6_1_SOL: [47.4, 49.9, 51.4, 52.6, 52.9],
        CLAUDE_OPUS_5_5: [48.3, 54.7, 55.6, 57.5, 61.4],
        CLAUDE_SONNET_5_5: [36.2, 39.8, 45.8, 50.0, 55.0],
    }, (30, 70), 10),
    Metric("CritPt v1", "% · Artificial Analysis; historical run, original task set", {
        GPT_6_ASTRA: [26.3, 29.1, 28.9, 31.4, 31.7],
        GPT_6_1_SOL: [24.9, 27.7, 30.0, 31.7, 31.7],
        CLAUDE_OPUS_5_5: [17.7, 27.7, 30.9, 31.7, 31.7],
        CLAUDE_SONNET_5_5: [11.4, 16.9, 24.6, 31.1, 31.4],
    }, (0, 40), 10),
]


@dataclass(frozen=True)
class ReportedMetric:
    """A benchmark with one reported score per model, at whatever effort its reporter ran; drawn as bars."""
    name: str
    unit_and_source: str
    scores: dict[Model, tuple[float, str]]  # score, and the effort level the reporter ran it at
    x_max: float = 100
    tick_step: float = 25
    decimals: int = 1
    prices: dict[Model, float] = field(default_factory=dict)

    @property
    def models(self) -> list[Model]:
        return [model for model in MODELS if model in self.scores]

    @property
    def costs(self) -> dict[Model, Scores] | None:
        return COSTS.get(self.name)

    @property
    def cost_unit(self) -> str:
        return COST_UNITS.get(self.name, DEFAULT_COST_UNIT)


# One score per model, at the effort level its reporter ran; sources in sources/*.json.
REPORTED = [
    ReportedMetric("Vals Index", "% · v2.2 · Vals AI, one harness for all models", {
        GEMINI_4_NEON: (70.87, 'xhigh'),
        GPT_6_ASTRA: (65.02, "max"),
        GPT_6_1_SOL: (63.94, "max"),
        CLAUDE_FABLE_5_2: (71.31, "high"),
        CLAUDE_OPUS_5_5: (70.14, "max"),
        CLAUDE_SONNET_5_5: (70.85, "max"),
        GEMINI_4_CARBON: (70.45, "high"),
        GPT_6_2_ASTRA: (67.66, 'max'),
        GPT_6_2_SOL: (66.06, 'max'),
        GEMINI_4_HYDROGEN: (68.49, 'xhigh'),
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
        GEMINI_4_CARBON: (64.0, 'high'),
    }),
    ReportedMetric("Vibe Code Bench v1.1", "% · Vals AI, OpenHands harness for all models", {
        GEMINI_4_NEON: (93.7, 'xhigh'),
        GPT_6_ASTRA: (89.59, "max"),
        GPT_6_1_SOL: (88.93, "max"),
        CLAUDE_FABLE_5_2: (93.77, "high"),
        CLAUDE_OPUS_5_5: (90.29, "max"),
        CLAUDE_SONNET_5_5: (92.39, "max"),
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
    }, x_max=1500, tick_step=250, decimals=0),
    ReportedMetric('SWE-sweep (provider harness)', '% subtask-weighted reward · Google runs · provider-specific agents/subagents', {
        GEMINI_4_NEON: (39, 'xhigh'),
        CLAUDE_OPUS_5_5: (10.1, 'not stated'),
        GPT_6_2_SOL: (8.3, 'not stated'),
    }, decimals=1),
    ReportedMetric('SWE-sweep (Mini-SWE vision)', '% subtask-weighted reward · Google runs · mini-swe-agent vision', {
        GEMINI_4_NEON: (12.8, 'xhigh'),
        CLAUDE_OPUS_5_5: (3.6, 'not stated'),
        GPT_6_2_SOL: (11.6, 'not stated'),
    }, decimals=1),
    ReportedMetric('Chartography (no tools, Google)', '% · no tools · Google Neon/Sol runs; Opus system card', {
        GEMINI_4_NEON: (73.5, 'xhigh'),
        CLAUDE_OPUS_5_5: (66.3, 'not stated'),
        GPT_6_2_SOL: (75.1, 'not stated'),
    }, decimals=1),
    ReportedMetric('LVBench (Google)', '% · vision-only · Google runs · unequal frame budgets', {
        GEMINI_4_NEON: (89, 'xhigh'),
        CLAUDE_OPUS_5_5: (83.7, 'not stated'),
        GPT_6_2_SOL: (87.6, 'not stated'),
    }, decimals=1),
    ReportedMetric('GraphWalks (256k–1M, Google)', '% BFS F1 · 200 problems · Google runs', {
        GEMINI_4_NEON: (95.2, 'xhigh'),
        CLAUDE_OPUS_5_5: (66.8, 'not stated'),
        GPT_6_2_SOL: (80.1, 'not stated'),
    }, decimals=1),

    ReportedMetric('Chartography v1.1 (agentic)', '% correct · Surge v1.1 agentic harness; not Google’s no-tools run', {
        GPT_6_2_ASTRA: (90.7, 'max'),
        CLAUDE_OPUS_5_5: (89.6, 'max'),
        GPT_6_ASTRA: (88.6, 'max'),
        GPT_6_2_SOL: (87.7, 'max'),
        GEMINI_4_HYDROGEN: (87.2, 'xhigh'),
        GEMINI_4_NEON: (86.6, 'high'),
        GEMINI_4_CARBON: (85.5, 'high'),
        CLAUDE_FABLE_5_2: (80.8, 'max'),
    }, decimals=1),
    ReportedMetric('ComplexConstraints v1.1 (agentic)', '% full-rubric pass · Surge v1.1 agentic · 75 tasks × 10 trials', {
        GEMINI_4_HYDROGEN: (73.7, 'xhigh'),
        GEMINI_4_NEON: (72.9, 'high'),
        GEMINI_4_CARBON: (70.9, 'high'),
        GPT_6_ASTRA: (70.8, 'max'),
        GPT_6_1_SOL: (70.1, 'max'),
        GPT_6_2_ASTRA: (69.6, 'max'),
        GPT_6_2_SOL: (69.5, 'max'),
        CLAUDE_SONNET_5_5: (67.2, 'max'),
        CLAUDE_FABLE_5_2: (64.5, 'max'),
        CLAUDE_OPUS_5_5: (64.4, 'max'),
    }, decimals=1),
    ReportedMetric('DAYJOB: Finance', '% task pass, 100% rubric threshold · Surge · 80 tasks × 5 trials', {
        GEMINI_4_NEON: (50.5, 'high'),
        GPT_6_2_ASTRA: (45.8, 'max'),
        CLAUDE_FABLE_5_2: (43.7, 'max'),
        CLAUDE_OPUS_5_5: (42.5, 'max'),
        CLAUDE_SONNET_5_5: (40.5, 'max'),
        GEMINI_4_HYDROGEN: (38.5, 'xhigh'),
        GPT_6_ASTRA: (37.3, 'max'),
        GPT_6_1_SOL: (33.5, 'max'),
        GPT_6_2_SOL: (32.8, 'max'),
        GEMINI_4_CARBON: (23.8, 'high'),
    }, decimals=1),
    ReportedMetric('DAYJOB: Healthcare', '% task pass, 100% rubric threshold · Surge · 50 tasks × 5 trials', {
        CLAUDE_OPUS_5_5: (48.3, 'max'),
        GEMINI_4_NEON: (47.2, 'high'),
        CLAUDE_FABLE_5_2: (45.0, 'max'),
        GEMINI_4_CARBON: (35.2, 'high'),
        GPT_6_2_ASTRA: (34.4, 'max'),
        CLAUDE_SONNET_5_5: (34.0, 'max'),
        GPT_6_ASTRA: (28.4, 'max'),
        GPT_6_1_SOL: (25.2, 'max'),
        GEMINI_4_HYDROGEN: (24.0, 'xhigh'),
        GPT_6_2_SOL: (17.2, 'max'),
    }, decimals=1),
    ReportedMetric('DAYJOB: Law (95% threshold)', '% pass@1, ≥95% rubric threshold · Surge · 71 tasks × 5 trials', {
        GPT_6_2_ASTRA: (41.4, 'max'),
        GPT_6_ASTRA: (36.6, 'max'),
        GPT_6_2_SOL: (32.7, 'max'),
        GPT_6_1_SOL: (31.6, 'max'),
        CLAUDE_SONNET_5_5: (26.8, 'max'),
        CLAUDE_FABLE_5_2: (26.5, 'max'),
        GEMINI_4_NEON: (26.2, 'high'),
        CLAUDE_OPUS_5_5: (23.7, 'max'),
        GEMINI_4_CARBON: (13.8, 'high'),
        GEMINI_4_HYDROGEN: (9.7, 'xhigh'),
    }, decimals=1),
    ReportedMetric('DAYJOB: Tax (95% threshold)', '% pass@1, ≥95% rubric threshold · Surge · 50 tasks × 5 trials', {
        CLAUDE_FABLE_5_2: (15.6, 'max'),
        GEMINI_4_NEON: (12.8, 'high'),
        CLAUDE_SONNET_5_5: (10.8, 'max'),
        CLAUDE_OPUS_5_5: (9.2, 'max'),
        GPT_6_2_ASTRA: (9.2, 'max'),
        GPT_6_ASTRA: (4.8, 'max'),
        GEMINI_4_CARBON: (4.8, 'high'),
        GPT_6_2_SOL: (4.8, 'max'),
        GPT_6_1_SOL: (4.0, 'max'),
        GEMINI_4_HYDROGEN: (3.6, 'xhigh'),
    }, decimals=1),
    ReportedMetric('EnterpriseBench: CoreCraft Agents', '% all-rubric task success · Surge · provider tools', {
        CLAUDE_OPUS_5_5: (74.4, 'max'),
        CLAUDE_SONNET_5_5: (70.8, 'max'),
        GPT_6_1_SOL: (50.3, 'max'),
        GPT_6_ASTRA: (42.6, 'max'),
    }, decimals=1),
    ReportedMetric('GDP.pdf v1.1 (agentic)', '% all-rubric task pass · Surge v1.1 agentic; not AA’s run', {
        GEMINI_4_CARBON: (56.4, 'high'),
        GEMINI_4_HYDROGEN: (54.2, 'xhigh'),
        GEMINI_4_NEON: (53.4, 'high'),
        CLAUDE_FABLE_5_2: (51.8, 'max'),
        GPT_6_1_SOL: (51.6, 'max'),
        CLAUDE_SONNET_5_5: (51.2, 'max'),
        GPT_6_ASTRA: (50.4, 'max'),
        GPT_6_2_ASTRA: (49.2, 'max'),
        CLAUDE_OPUS_5_5: (48.8, 'max'),
        GPT_6_2_SOL: (48.8, 'max'),
    }, decimals=1),
    ReportedMetric('GDP.xlsx', '% published score · Surge · 70 tasks × 5 trials; headline threshold unspecified', {
        GEMINI_4_NEON: (43.1, 'high'),
        GEMINI_4_HYDROGEN: (40.9, 'xhigh'),
        GEMINI_4_CARBON: (38.9, 'high'),
        CLAUDE_FABLE_5_2: (32.9, 'max'),
        CLAUDE_OPUS_5_5: (30.3, 'max'),
        GPT_6_2_ASTRA: (29.7, 'max'),
        CLAUDE_SONNET_5_5: (29.1, 'max'),
        GPT_6_ASTRA: (22.9, 'max'),
        GPT_6_2_SOL: (22.3, 'max'),
        GPT_6_1_SOL: (22.0, 'max'),
    }, decimals=1),
    ReportedMetric('HANDBOOK.md v1.1 Agents', '% task success · Surge v1.1 revised grading · 65 tasks × 5 trials', {
        CLAUDE_OPUS_5_5: (52.3, 'max'),
        CLAUDE_FABLE_5_2: (52.3, 'max'),
        GEMINI_4_NEON: (52.3, 'high'),
        GEMINI_4_CARBON: (49.8, 'high'),
        CLAUDE_SONNET_5_5: (47.7, 'max'),
        GPT_6_2_ASTRA: (45.8, 'max'),
        GEMINI_4_HYDROGEN: (44.6, 'xhigh'),
        GPT_6_2_SOL: (34.5, 'max'),
        GPT_6_ASTRA: (31.4, 'max'),
        GPT_6_1_SOL: (28.6, 'max'),
    }, decimals=1),
    ReportedMetric('Riemann-bench v1.1', '% pass@1 · Surge v1.1 corrected answer keys · 25 research-math problems', {
        GEMINI_4_NEON: (84.0, 'high'),
        CLAUDE_FABLE_5_2: (83.2, 'max'),
        GPT_6_ASTRA: (81.6, 'max'),
        GPT_6_2_SOL: (80.0, 'max'),
        GEMINI_4_CARBON: (80.0, 'high'),
        CLAUDE_OPUS_5_5: (80.0, 'max'),
        GPT_6_1_SOL: (79.2, 'max'),
        CLAUDE_SONNET_5_5: (76.8, 'max'),
        GPT_6_2_ASTRA: (76.0, 'max'),
    }, decimals=1),
    ReportedMetric('sudo L7', '% published engineering-task score · Surge · 60 tasks; threshold unspecified', {
        CLAUDE_FABLE_5_2: (52.2, 'max'),
        CLAUDE_SONNET_5_5: (50.6, 'max'),
        CLAUDE_OPUS_5_5: (46.1, 'max'),
        GPT_6_2_ASTRA: (38.3, 'max'),
        GEMINI_4_NEON: (38.3, 'high'),
        GPT_6_2_SOL: (36.1, 'max'),
        GPT_6_1_SOL: (33.9, 'max'),
        GEMINI_4_HYDROGEN: (31.7, 'xhigh'),
        GPT_6_ASTRA: (31.1, 'max'),
        GEMINI_4_CARBON: (30.6, 'high'),
    }, decimals=1),
    ReportedMetric('Vals Finance Index v1', '% · equal-weight Finance Agent/EMB/Tax composite · Vals AI', {
        GEMINI_4_NEON: (68.32, 'xhigh'),
        GPT_6_ASTRA: (55.64, 'max'),
        GPT_6_2_ASTRA: (57.31, 'max'),
        GPT_6_1_SOL: (55.81, 'max'),
        GPT_6_2_SOL: (56.66, 'max'),
        CLAUDE_FABLE_5_2: (63.58, 'high'),
        CLAUDE_OPUS_5_5: (65.34, 'max'),
        CLAUDE_SONNET_5_5: (64.53, 'max'),
        GEMINI_4_CARBON: (67.05, 'high'),
        GEMINI_4_HYDROGEN: (66.14, 'xhigh'),
    }, decimals=2),
    ReportedMetric('Vals Legal Index v1', '% · equal-weight Legal Research/HLAB composite · Vals AI', {
        GEMINI_4_NEON: (78.36, 'xhigh'),
        GPT_6_ASTRA: (68.39, 'max'),
        GPT_6_2_ASTRA: (69.68, 'max'),
        GPT_6_1_SOL: (68.72, 'max'),
        GPT_6_2_SOL: (66.68, 'max'),
        CLAUDE_FABLE_5_2: (69.18, 'high'),
        CLAUDE_OPUS_5_5: (72.37, 'max'),
        CLAUDE_SONNET_5_5: (68.02, 'max'),
        GEMINI_4_CARBON: (75.93, 'high'),
        GEMINI_4_HYDROGEN: (73.63, 'xhigh'),
    }, decimals=2),
    ReportedMetric('Vals Science Index v1 (Vals)', '% · BioMystery/MysteryMechanism/TB-Science composite · Vals AI; not OpenAI’s run', {
        GEMINI_4_NEON: (62.63, 'xhigh'),
        GPT_6_ASTRA: (65.09, 'max'),
        GPT_6_2_ASTRA: (68.44, 'max'),
        GPT_6_1_SOL: (59.63, 'max'),
        GPT_6_2_SOL: (57.76, 'max'),
        CLAUDE_FABLE_5_2: (63.74, 'high'),
        CLAUDE_OPUS_5_5: (58.65, 'max'),
        CLAUDE_SONNET_5_5: (59.12, 'max'),
    }, decimals=2),
    ReportedMetric('EMB v1.1', '% financial modeling spreadsheet score · Vals AI', {
        GEMINI_4_NEON: (76.46, 'xhigh'),
        GPT_6_ASTRA: (72.68, 'max'),
        GPT_6_2_ASTRA: (76.03, 'max'),
        GPT_6_1_SOL: (71.09, 'max'),
        GPT_6_2_SOL: (74.29, 'max'),
        CLAUDE_FABLE_5_2: (77.38, 'high'),
        CLAUDE_OPUS_5_5: (75.84, 'max'),
        CLAUDE_SONNET_5_5: (75.9, 'max'),
        GEMINI_4_CARBON: (76.47, 'high'),
        GEMINI_4_HYDROGEN: (75.8, 'xhigh'),
    }, decimals=2),
    ReportedMetric('Finance Agent v2.1', '% financial research accuracy · Vals AI', {
        GEMINI_4_NEON: (68.56, 'xhigh'),
        GPT_6_ASTRA: (60.43, 'max'),
        GPT_6_2_ASTRA: (60.75, 'max'),
        GPT_6_1_SOL: (61.82, 'max'),
        GPT_6_2_SOL: (58.91, 'max'),
        CLAUDE_FABLE_5_2: (69.47, 'high'),
        CLAUDE_OPUS_5_5: (67.85, 'max'),
        CLAUDE_SONNET_5_5: (67.28, 'max'),
        GEMINI_4_CARBON: (67.16, 'high'),
        GEMINI_4_HYDROGEN: (65.12, 'xhigh'),
    }, decimals=2),
    ReportedMetric('Legal Research Bench v1', '% legal-research task pass · Vals AI', {
        GEMINI_4_NEON: (56.25, 'xhigh'),
        GPT_6_ASTRA: (39.42, 'max'),
        GPT_6_2_ASTRA: (42.79, 'max'),
        GPT_6_1_SOL: (38.46, 'max'),
        GPT_6_2_SOL: (37.02, 'max'),
        CLAUDE_FABLE_5_2: (46.15, 'high'),
        CLAUDE_OPUS_5_5: (50.48, 'max'),
        CLAUDE_SONNET_5_5: (48.08, 'max'),
        GEMINI_4_CARBON: (55.77, 'high'),
        GEMINI_4_HYDROGEN: (53.85, 'xhigh'),
    }, decimals=2),
    ReportedMetric('MysteryMechanism v1', '% mechanistic chemistry inference · Vals AI', {
        GEMINI_4_NEON: (45.05, 'xhigh'),
        GPT_6_ASTRA: (53.15, 'max'),
        GPT_6_2_ASTRA: (53.15, 'max'),
        GPT_6_1_SOL: (46.4, 'max'),
        GPT_6_2_SOL: (36.94, 'max'),
        CLAUDE_FABLE_5_2: (51.8, 'high'),
        CLAUDE_OPUS_5_5: (49.55, 'max'),
        CLAUDE_SONNET_5_5: (49.1, 'max'),
    }, decimals=2),
    ReportedMetric('Tax Agent Bench v1', '% tax research accuracy · Vals AI', {
        GEMINI_4_NEON: (54.89, 'xhigh'),
        GPT_6_ASTRA: (20.72, 'max'),
        GPT_6_2_ASTRA: (21.84, 'max'),
        GPT_6_1_SOL: (21.75, 'max'),
        GPT_6_2_SOL: (24.84, 'max'),
        CLAUDE_FABLE_5_2: (32.09, 'high'),
        CLAUDE_OPUS_5_5: (44.54, 'max'),
        CLAUDE_SONNET_5_5: (41.96, 'max'),
        GEMINI_4_CARBON: (51.79, 'high'),
        GEMINI_4_HYDROGEN: (52.31, 'xhigh'),
    }, decimals=2),
    ReportedMetric('BioMysteryBench v1', '% computational biology task pass · Vals AI · Terminus 2', {
        GEMINI_4_NEON: (80.0, 'xhigh'),
        GPT_6_ASTRA: (79.26, 'max'),
        GPT_6_2_ASTRA: (80.74, 'max'),
        GPT_6_1_SOL: (79.63, 'max'),
        GPT_6_2_SOL: (77.78, 'max'),
        CLAUDE_FABLE_5_2: (83.7, 'high'),
        CLAUDE_OPUS_5_5: (79.26, 'max'),
        CLAUDE_SONNET_5_5: (81.11, 'max'),
    }, decimals=2),
    ReportedMetric('HLAB-Vals v1.1', '% all-rubric task pass · Vals AI; not Harvey LAB-AA', {
        GEMINI_4_NEON: (19.58, 'xhigh'),
        GPT_6_ASTRA: (7.08, 'max'),
        GPT_6_2_ASTRA: (16.25, 'max'),
        GPT_6_1_SOL: (6.25, 'max'),
        GPT_6_2_SOL: (12.08, 'max'),
        CLAUDE_FABLE_5_2: (5.0, 'high'),
        CLAUDE_OPUS_5_5: (9.17, 'max'),
        CLAUDE_SONNET_5_5: (10.42, 'max'),
        GEMINI_4_CARBON: (17.5, 'high'),
        GEMINI_4_HYDROGEN: (11.25, 'xhigh'),
    }, decimals=2),
    ReportedMetric('Terminal-Bench 4.0 (Vals)', '% avg@3 · Vals AI Mini-SWE-agent; not AA’s run', {
        GEMINI_4_NEON: (61.62, 'xhigh'),
        GPT_6_ASTRA: (59.6, 'max'),
        GPT_6_2_ASTRA: (63.13, 'max'),
        GPT_6_1_SOL: (55.05, 'max'),
        GPT_6_2_SOL: (60.61, 'max'),
        CLAUDE_FABLE_5_2: (65.15, 'high'),
        CLAUDE_OPUS_5_5: (65.15, 'max'),
        CLAUDE_SONNET_5_5: (64.14, 'max'),
        GEMINI_4_CARBON: (63.13, 'high'),
        GEMINI_4_HYDROGEN: (54.04, 'xhigh'),
    }, decimals=2),
    ReportedMetric('Terminal-Bench Science 0.1 (Vals)', '% single-run task pass · Vals AI Mini-SWE-agent; infrastructure retries', {
        GEMINI_4_NEON: (62.86, 'xhigh'),
        GPT_6_ASTRA: (62.86, 'max'),
        GPT_6_2_ASTRA: (71.43, 'max'),
        GPT_6_1_SOL: (52.86, 'max'),
        GPT_6_2_SOL: (58.57, 'max'),
        CLAUDE_FABLE_5_2: (55.71, 'high'),
        CLAUDE_OPUS_5_5: (47.14, 'max'),
        CLAUDE_SONNET_5_5: (47.14, 'max'),
    }, decimals=2),
    ReportedMetric('Terminal-Bench Science 0.1 (public board)', '% average resolution · public provider agents · 70 tasks × 3 trials', {
        GPT_6_ASTRA: (68.1, 'max'),
        CLAUDE_OPUS_5_5: (63.33, 'max'),
    }, decimals=2),
    ReportedMetric('CWE-bench v2 (250 tasks)', '% programmatic pass@1 · public+held-out 250 tasks · provider agents · four rollouts/task', {
        CLAUDE_FABLE_5_2: (75.0, 'high'),
        GEMINI_4_NEON: (70.7, 'high'),
        GEMINI_4_HYDROGEN: (68.1, 'high'),
        GEMINI_4_CARBON: (67.3, 'high'),
        CLAUDE_OPUS_5_5: (67.1, 'high'),
        GPT_6_2_ASTRA: (66.8, 'high'),
        GPT_6_2_SOL: (66.0, 'high'),
        GPT_6_ASTRA: (64.2, 'high'),
        CLAUDE_SONNET_5_5: (61.4, 'high'),
    }, decimals=2),
    ReportedMetric('SEC-bench Pro 260505 (183 tasks)', '% pass@1 · provider-reported · 183 JS-engine tasks; not newer 344-task split', {
        GEMINI_4_NEON: (90.5, 'xhigh'),
        GPT_6_2_SOL: (88.34, 'not stated'),
        GEMINI_4_CARBON: (88.2, 'not stated'),
        GPT_6_2_ASTRA: (86.75, 'not stated'),
        GPT_6_ASTRA: (85.4, 'not stated'),
        GPT_6_1_SOL: (78.8, 'not stated'),
    }, decimals=2),
    ReportedMetric('WebExploitBench v1.2 (277 vulnerabilities)', '% success · board’s Pass@3 (AVG.) · 15 apps, provider agents; effort not stated', {
        GEMINI_4_NEON: (51.26, 'not stated'),
        GEMINI_4_CARBON: (44.65, 'not stated'),
        GPT_6_ASTRA: (38.99, 'not stated'),
        CLAUDE_OPUS_5_5: (37.06, 'not stated'),
    }, decimals=2),
    ReportedMetric('AutomationBench 1.0.6 (nonstandard efforts)', '% strict task pass · Zapier · exact effort labels; grouped under Not stated filter', {
        GPT_6_ASTRA: (25.27, 'none'),
        CLAUDE_SONNET_5_5: (18.57, 'between tools'),
    }, decimals=2, prices={GPT_6_ASTRA: 1.28, CLAUDE_SONNET_5_5: 0.30}),
    ReportedMetric('Terminal-Bench Science 0.1 (Google Neon)', '% average reward · Google mini-swe-agent vision · five attempts/task', {
        GEMINI_4_NEON: (70.5, 'xhigh'),
    }, decimals=1),
    ReportedMetric('AutoBaxBench easy (functional)', '% pass@1 · AutoBaxBuilder · no security prompt; mixed effort where labeled', {
        CLAUDE_FABLE_5_2: (89.29, 'highest/high mixed'),
        CLAUDE_OPUS_5_5: (92.86, 'highest/high mixed'),
        GEMINI_4_CARBON: (87.14, 'highest (level not stated)'),
        GPT_6_ASTRA: (91.43, 'highest (level not stated)'),
        GEMINI_4_NEON: (85.0, 'highest (level not stated)'),
    }, x_max=100, tick_step=25, decimals=2),
    ReportedMetric('AutoBaxBench easy (functional + secure)', '% pass@1 · AutoBaxBuilder · no security prompt; mixed effort where labeled', {
        CLAUDE_FABLE_5_2: (88.57, 'highest/high mixed'),
        CLAUDE_OPUS_5_5: (80.71, 'highest/high mixed'),
        GEMINI_4_CARBON: (61.43, 'highest (level not stated)'),
        GPT_6_ASTRA: (59.29, 'highest (level not stated)'),
        GEMINI_4_NEON: (71.43, 'highest (level not stated)'),
    }, x_max=100, tick_step=25, decimals=2),
    ReportedMetric('AutoBaxBench medium (functional)', '% pass@1 · AutoBaxBuilder · no security prompt; mixed effort where labeled', {
        CLAUDE_FABLE_5_2: (91.43, 'highest/high mixed'),
        CLAUDE_OPUS_5_5: (87.5, 'highest/high mixed'),
        GEMINI_4_CARBON: (81.43, 'highest (level not stated)'),
        GPT_6_ASTRA: (86.79, 'highest (level not stated)'),
        GEMINI_4_NEON: (79.64, 'highest (level not stated)'),
    }, x_max=100, tick_step=25, decimals=2),
    ReportedMetric('AutoBaxBench medium (functional + secure)', '% pass@1 · AutoBaxBuilder · no security prompt; mixed effort where labeled', {
        CLAUDE_FABLE_5_2: (77.86, 'highest/high mixed'),
        CLAUDE_OPUS_5_5: (73.21, 'highest/high mixed'),
        GEMINI_4_CARBON: (60.0, 'highest (level not stated)'),
        GPT_6_ASTRA: (56.79, 'highest (level not stated)'),
        GEMINI_4_NEON: (66.07, 'highest (level not stated)'),
    }, x_max=100, tick_step=25, decimals=2),
    ReportedMetric('AutoBaxBench hard (functional)', '% pass@1 · AutoBaxBuilder · no security prompt; mixed effort where labeled', {
        CLAUDE_FABLE_5_2: (78.57, 'highest/high mixed'),
        CLAUDE_OPUS_5_5: (71.43, 'highest/high mixed'),
        GEMINI_4_CARBON: (88.57, 'highest (level not stated)'),
        GPT_6_ASTRA: (93.57, 'highest (level not stated)'),
        GEMINI_4_NEON: (77.14, 'highest (level not stated)'),
    }, x_max=100, tick_step=25, decimals=2),
    ReportedMetric('AutoBaxBench hard (functional + secure)', '% pass@1 · AutoBaxBuilder · no security prompt; mixed effort where labeled', {
        CLAUDE_FABLE_5_2: (67.86, 'highest/high mixed'),
        CLAUDE_OPUS_5_5: (67.86, 'highest/high mixed'),
        GEMINI_4_CARBON: (73.57, 'highest (level not stated)'),
        GPT_6_ASTRA: (57.14, 'highest (level not stated)'),
        GEMINI_4_NEON: (76.43, 'highest (level not stated)'),
    }, x_max=100, tick_step=25, decimals=2),
    ReportedMetric('ExploitGym (2h timeout)', 'intended-vulnerability exploits / 869 · provider-reported; effort not stated', {
        CLAUDE_OPUS_5_5: (289.0, 'not stated'),
    }, x_max=900, tick_step=200, decimals=0),
    ReportedMetric('ExploitGym (6h timeout)', 'intended-vulnerability exploits / 869 · provider-reported; effort not stated', {
        CLAUDE_OPUS_5_5: (300.0, 'not stated'),
    }, x_max=900, tick_step=200, decimals=0),
    ReportedMetric('ExploitGym (token-budgeted)', 'intended-vulnerability exploits / 869 · provider-reported; effort not stated · approximate counts derived by board; output cap unspecified', {
        GPT_6_ASTRA: (368.0, 'not stated'),
        GPT_6_1_SOL: (305.0, 'not stated'),
    }, x_max=900, tick_step=200, decimals=0),
    ReportedMetric('Code Migration v1.1 (Vals Index subset)', '% hidden-test pass · Vals v1.1 Pi agent · 50 CLI + 10 COBOL subset · weighted 75:25', {
        CLAUDE_SONNET_5_5: (87.37, 'max'),
        CLAUDE_FABLE_5_2: (85.85, 'high'),
        GPT_6_2_SOL: (85.35, 'max'),
        GPT_6_2_ASTRA: (83.59, 'max'),
        GEMINI_4_HYDROGEN: (82.67, 'xhigh'),
        CLAUDE_OPUS_5_5: (80.49, 'max'),
        GEMINI_4_CARBON: (80.05, 'high'),
        GPT_6_ASTRA: (78.03, 'max'),
        GEMINI_4_NEON: (75.76, 'xhigh'),
        GPT_6_1_SOL: (75.14, 'max'),
    }, x_max=100, tick_step=25, decimals=2),
    ReportedMetric('Code Migration v1.1 (Vals full test set)', '% hidden-test pass · Vals v1.1 Pi agent · 120 CLI + 10 COBOL full test set · weighted 75:25', {
        CLAUDE_SONNET_5_5: (86.88, 'max'),
        CLAUDE_FABLE_5_2: (83.27, 'high'),
        CLAUDE_OPUS_5_5: (81.01, 'max'),
        GPT_6_ASTRA: (80.58, 'max'),
        GPT_6_1_SOL: (77.32, 'max'),
    }, x_max=100, tick_step=25, decimals=2),
]

# Each chart appears once, under the kind of task it asks the model to do.
SECTION_CHARTS: dict[str, list[str]] = {
    "Aggregates": ['Vals Index (Vals reasoning study)', 'Vals Finance Index v1', 'Vals Legal Index v1', "AA Intelligence Index", "Vals Index"],
    "Intelligence & knowledge": ['ComplexConstraints v1.1 (agentic)', "Agents' Last Exam v1.1 (public + Google)", 'Extended NYT Connections (940)', 'Extended NYT Connections (newest 100)', 'GraphWalks (256k–1M, Google)', "HLE-Diamond", "Humanity's Last Exam", "ARC-AGI-2", "AA-Omniscience Index", "AA-LCR", "Agents' Last Exam v1.1",
                                 "LifeVal"],
    "Coding & security": ['AutoBaxBench easy (functional)', 'AutoBaxBench easy (functional + secure)', 'AutoBaxBench medium (functional)', 'AutoBaxBench medium (functional + secure)', 'AutoBaxBench hard (functional)', 'AutoBaxBench hard (functional + secure)', 'ExploitGym (2h timeout)', 'ExploitGym (6h timeout)', 'ExploitGym (token-budgeted)', 'Code Migration v1.1 (Vals Index subset)', 'Code Migration v1.1 (Vals full test set)', 'sudo L7', 'Vibe Code Bench v1.1 (Vals reasoning study)', 'Terminal-Bench 4.0 (Vals)', 'Terminal-Bench 4.0 (Vals) (Vals reasoning study)', 'Terminal-Bench 4.1 (provider agents)', 'FrontierCode 2.0 (Cognition)', 'CWE-bench v2 (250 tasks)', 'SEC-bench Pro 260505 (183 tasks)', 'WebExploitBench v1.2 (277 vulnerabilities)', 'SWE-sweep (provider harness)', 'SWE-sweep (Mini-SWE vision)', "AA Index coding category", "Terminal-Bench 4.0", "Terminal-Bench 2.1", "Terminal-Bench 2.1 (Microsoft)", "FrontierCode-AA 2.0", "FrontierCode-AA 1.1", "FrontierCode 2.0", "FrontierCode 1.1 Main",
                          "DeepSWE v1.1", "CursorBench 4.1", "CursorBench 4.0", "Vibe Code Bench v1.1", "SWE-Bench Pro", "ITBench-AA",
                          "SecureSWE", "PatchBench", "ExploitBench – Internal Port (June–August 2026)"],
    "Science & engineering": ['Riemann-bench v1.1', 'Vals Science Index v1 (Vals)', 'MysteryMechanism v1', 'BioMysteryBench v1', 'Terminal-Bench Science 0.1 (Vals)', 'Terminal-Bench Science 0.1 (public board)', 'Terminal-Bench Science 0.1 (Google Neon)', "CritPt v2", "CritPt v1", "GPQA Diamond (AA)", "GPQA Diamond (OpenAI)", "Terminal-Bench Science 0.1",
                              "SciCode", "Vals Science Index v1", "BenchCAD 2.1 Core"],
    "Machine-learning research": ["Internal Research Debugging", "KernelGen 1P", "NanoGPT v5", "PostTrainBench Lite",
                                  "MLE-Bench Revised"],
    "Professional work": ['DAYJOB: Finance', 'DAYJOB: Law (95% threshold)', 'DAYJOB: Tax (95% threshold)', 'EnterpriseBench: CoreCraft Agents', 'GDP.pdf v1.1 (agentic)', 'GDP.xlsx', 'HANDBOOK.md v1.1 Agents', 'EMB v1.1', 'EMB v1.1 (Vals reasoning study)', 'Finance Agent v2.1', 'Finance Agent v2.1 (Vals reasoning study)', 'Legal Research Bench v1', 'Legal Research Bench v1 (Vals reasoning study)', 'Tax Agent Bench v1', 'Tax Agent Bench v1 (Vals reasoning study)', 'HLAB-Vals v1.1', 'HLAB-Vals v1.1 (Vals reasoning study)', 'AutomationBench 1.0.6 (Zapier)', 'AutomationBench 1.0.6 (nonstandard efforts)', "GDPval-AA", "GDPval v2 (Internal)", "AA-Briefcase", "MKA", "GDP.pdf", "AA-AnalystAgent",
                          "Harvey LAB-AA v1.1", "tau3-Banking", "EnterpriseOps-Gym-AA", "AutomationBench-AA",
                          "AutomationBench 1.0.6"],
    "Health": ['DAYJOB: Healthcare', "MLCR-AA", "HealthBench Professional (AA)", "HealthBench Professional (OpenAI)", "MentalHealthBench"],
    "Multimodal tasks": ['Chartography v1.1 (agentic)', 'Chartography (no tools, Google)', 'LVBench (Google)', "MMMU-Pro", "VIALS-AA", "AA-3D"],
}


def sections_from(chart_names: dict[str, list[str]]) -> list[tuple[str, list[Metric | ReportedMetric]]]:
    """Resolve section chart names to charts, raising ValueError unless every chart is placed exactly once."""
    by_name = {chart.name: chart for chart in [*CURVES, *REPORTED]}
    placed = sorted(name for names in chart_names.values() for name in names)
    if placed != sorted(by_name) or len(by_name) != len(CURVES) + len(REPORTED):
        raise ValueError(f"SECTION_CHARTS must place every chart exactly once. "
                         f"Missing: {sorted(set(by_name) - set(placed))}. Extra or repeated: "
                         f"{sorted(name for name in placed if name not in by_name or placed.count(name) > 1)}")
    return [(section, [by_name[name] for name in names]) for section, names in chart_names.items()]


SECTIONS = sections_from(SECTION_CHARTS)

@dataclass(frozen=True)
class BenchmarkVersion:
    label: str
    runners: dict[str, str]


BENCHMARK_VERSIONS = {
    "Terminal-Bench": [
        BenchmarkVersion("4.1", {"Terminal-Bench 4.1 (provider agents)": "Public provider-agent board"}),
        BenchmarkVersion("4.0", {"Terminal-Bench 4.0": "Artificial Analysis", "Terminal-Bench 4.0 (Vals)": "Vals Mini-SWE-agent"}),
        BenchmarkVersion("2.1", {"Terminal-Bench 2.1": "Artificial Analysis", "Terminal-Bench 2.1 (Microsoft)": "Microsoft Copilot CLI"}),
    ],
    "FrontierCode": [
        BenchmarkVersion("2.0", {"FrontierCode-AA 2.0": "Artificial Analysis", "FrontierCode 2.0": "OpenAI", "FrontierCode 2.0 (Cognition)": "Cognition"}),
        BenchmarkVersion("1.1", {"FrontierCode 1.1 Main": "Cognition Main", "FrontierCode-AA 1.1": "Artificial Analysis via Microsoft"}),
    ],
    "Humanity's Last Exam": [
        BenchmarkVersion("Diamond", {"HLE-Diamond": "Artificial Analysis · 1,000-question subset"}),
        BenchmarkVersion("Original full set", {"Humanity's Last Exam": "Artificial Analysis · full set"}),
    ],
    "CritPt": [
        BenchmarkVersion("2", {"CritPt v2": "Artificial Analysis · hard subset"}),
        BenchmarkVersion("1", {"CritPt v1": "Artificial Analysis · original task set"}),
    ],
    "CursorBench": [
        BenchmarkVersion("4.1", {"CursorBench 4.1": "Cursor"}),
        BenchmarkVersion("4.0", {"CursorBench 4.0": "Cursor"}),
    ],
    "SEC-bench Pro": [
        BenchmarkVersion("260617", {}),
        BenchmarkVersion("260505", {"SEC-bench Pro 260505 (183 tasks)": "Provider-reported · 183 tasks"}),
    ],
}

# US dollars per task of each benchmark at each effort level, from the same AA records (ARC Prize for ARC-AGI-2).
# AA weightedCostPerTask divided by its index weight; the coding category uses the same 15:10 weights as its score.
COSTS: dict[str, dict[Model, Scores]] = {
    "Terminal-Bench 2.1 (Microsoft)": {
        MAI_CODE_2: [None, None, None, None, 0.081],
        GPT_6_1_SOL: [None, None, None, None, 0.265],
        CLAUDE_OPUS_5_5: [None, None, None, None, 1.842],
    },
    "FrontierCode-AA 1.1": {
        MAI_CODE_2: [None, None, None, None, 0.310],
        GPT_6_1_SOL: [None, None, None, None, 0.960],
        CLAUDE_OPUS_5_5: [None, None, None, None, 8.430],
    },
    'Code Migration v1.1 (Vals Index subset)': {
        CLAUDE_SONNET_5_5: [None, None, None, None, 45.4],
        CLAUDE_FABLE_5_2: [None, None, 68.7, None, None],
        GPT_6_2_SOL: [None, None, None, None, 9.76],
        GPT_6_2_ASTRA: [None, None, None, None, 34.0],
        GEMINI_4_HYDROGEN: [None, None, None, 45.6, None],
        CLAUDE_OPUS_5_5: [None, None, None, None, 72.3],
        GEMINI_4_CARBON: [None, None, 33.7, None, None],
        GPT_6_ASTRA: [None, None, None, None, 66.6],
        GEMINI_4_NEON: [None, None, None, 18.1, None],
        GPT_6_1_SOL: [None, None, None, None, 9.94],
    },
    'Code Migration v1.1 (Vals full test set)': {
        CLAUDE_SONNET_5_5: [None, None, None, None, 43.9],
        CLAUDE_FABLE_5_2: [None, None, 69.2, None, None],
        CLAUDE_OPUS_5_5: [None, None, None, None, 72.4],
        GPT_6_ASTRA: [None, None, None, None, 62.1],
        GPT_6_1_SOL: [None, None, None, None, 9.51],
    },
    'Vals Index (Vals reasoning study)': {
        GPT_6_ASTRA: [4.0, None, 8.63, None, 22.2],
        CLAUDE_OPUS_5_5: [4.26, None, 10.8, None, 26.5],
        GPT_6_2_ASTRA: [2.81, 4.32, 5.81, 7.0, 11.1],
        CLAUDE_FABLE_5_2: [None, None, 20.2, None, None],
    },
    'Vals Finance Index v1': {
        GEMINI_4_NEON: [None, None, None, 4.88, None],
        GPT_6_ASTRA: [None, None, None, None, 6.48],
        GPT_6_2_ASTRA: [None, None, None, None, 6.23],
        GPT_6_1_SOL: [None, None, None, None, 1.36],
        GPT_6_2_SOL: [None, None, None, None, 1.77],
        CLAUDE_FABLE_5_2: [None, None, 4.94, None, None],
        CLAUDE_OPUS_5_5: [None, None, None, None, 10.9],
        CLAUDE_SONNET_5_5: [None, None, None, None, 7.4],
        GEMINI_4_CARBON: [None, None, 6.46, None, None],
        GEMINI_4_HYDROGEN: [None, None, None, 3.8, None],
    },
    'Vals Legal Index v1': {
        GEMINI_4_NEON: [None, None, None, 6.1, None],
        GPT_6_ASTRA: [None, None, None, None, 13.9],
        GPT_6_2_ASTRA: [None, None, None, None, 9.35],
        GPT_6_1_SOL: [None, None, None, None, 2.75],
        GPT_6_2_SOL: [None, None, None, None, 2.8],
        CLAUDE_FABLE_5_2: [None, None, 8.88, None, None],
        CLAUDE_OPUS_5_5: [None, None, None, None, 19.9],
        CLAUDE_SONNET_5_5: [None, None, None, None, 13.4],
        GEMINI_4_CARBON: [None, None, 7.2, None, None],
        GEMINI_4_HYDROGEN: [None, None, None, 4.47, None],
    },
    'Vals Science Index v1 (Vals)': {
        GEMINI_4_NEON: [None, None, None, 8.26, None],
        GPT_6_ASTRA: [None, None, None, None, 8.03],
        GPT_6_2_ASTRA: [None, None, None, None, 4.76],
        GPT_6_1_SOL: [None, None, None, None, 1.36],
        GPT_6_2_SOL: [None, None, None, None, 1.12],
        CLAUDE_FABLE_5_2: [None, None, 8.79, None, None],
        CLAUDE_OPUS_5_5: [None, None, None, None, 8.71],
        CLAUDE_SONNET_5_5: [None, None, None, None, 8.5],
    },
    'EMB v1.1': {
        GEMINI_4_NEON: [None, None, None, 3.82, None],
        GPT_6_ASTRA: [None, None, None, None, 5.83],
        GPT_6_2_ASTRA: [None, None, None, None, 2.8],
        GPT_6_1_SOL: [None, None, None, None, 1.14],
        GPT_6_2_SOL: [None, None, None, None, 0.841],
        CLAUDE_FABLE_5_2: [None, None, 6.67, None, None],
        CLAUDE_OPUS_5_5: [None, None, None, None, 9.33],
        CLAUDE_SONNET_5_5: [None, None, None, None, 6.53],
        GEMINI_4_CARBON: [None, None, 5.76, None, None],
        GEMINI_4_HYDROGEN: [None, None, None, 3.17, None],
    },
    'EMB v1.1 (Vals reasoning study)': {
        GPT_6_ASTRA: [0.789, None, 2.58, None, 4.8],
        CLAUDE_OPUS_5_5: [0.525, None, 1.56, None, 6.8],
        GPT_6_2_ASTRA: [0.464, 0.64, 1.22, 1.89, 2.49],
        CLAUDE_FABLE_5_2: [2.24, None, 6.44, 12.3, 25.2],
    },
    'Finance Agent v2.1': {
        GEMINI_4_NEON: [None, None, None, 5.85, None],
        GPT_6_ASTRA: [None, None, None, None, 7.82],
        GPT_6_2_ASTRA: [None, None, None, None, 7.98],
        GPT_6_1_SOL: [None, None, None, None, 1.63],
        GPT_6_2_SOL: [None, None, None, None, 2.06],
        CLAUDE_FABLE_5_2: [None, None, 4.83, None, None],
        CLAUDE_OPUS_5_5: [None, None, None, None, 8.91],
        CLAUDE_SONNET_5_5: [None, None, None, None, 6.95],
        GEMINI_4_CARBON: [None, None, 7.29, None, None],
        GEMINI_4_HYDROGEN: [None, None, None, 4.36, None],
    },
    'Finance Agent v2.1 (Vals reasoning study)': {
        GPT_6_ASTRA: [3.77, None, 5.63, None, 7.97],
        CLAUDE_OPUS_5_5: [0.855, None, 1.93, None, 9.01],
        GPT_6_2_ASTRA: [1.89, 2.62, 4.08, 5.16, 7.81],
        CLAUDE_FABLE_5_2: [3.19, None, 4.99, 7.22, 18.5],
    },
    'Legal Research Bench v1': {
        GEMINI_4_NEON: [None, None, None, 7.37, None],
        GPT_6_ASTRA: [None, None, None, None, 10.6],
        GPT_6_2_ASTRA: [None, None, None, None, 12.8],
        GPT_6_1_SOL: [None, None, None, None, 3.38],
        GPT_6_2_SOL: [None, None, None, None, 3.77],
        CLAUDE_FABLE_5_2: [None, None, 3.96, None, None],
        CLAUDE_OPUS_5_5: [None, None, None, None, 23.6],
        CLAUDE_SONNET_5_5: [None, None, None, None, 13.7],
        GEMINI_4_CARBON: [None, None, 8.74, None, None],
        GEMINI_4_HYDROGEN: [None, None, None, 6.27, None],
    },
    'Legal Research Bench v1 (Vals reasoning study)': {
        GPT_6_ASTRA: [1.59, None, 5.19, None, 11.3],
        CLAUDE_OPUS_5_5: [0.107, None, 0.525, None, 22.8],
        GPT_6_2_ASTRA: [0.361, 1.2, 4.23, 6.61, 12.5],
        CLAUDE_FABLE_5_2: [0.591, None, 3.79, 9.31, None],
    },
    'MysteryMechanism v1': {
        GEMINI_4_NEON: [None, None, None, 6.63, None],
        GPT_6_ASTRA: [None, None, None, None, 1.56],
        GPT_6_2_ASTRA: [None, None, None, None, 1.72],
        GPT_6_1_SOL: [None, None, None, None, 0.285],
        GPT_6_2_SOL: [None, None, None, None, 0.487],
        CLAUDE_FABLE_5_2: [None, None, 1.55, None, None],
        CLAUDE_OPUS_5_5: [None, None, None, None, 4.06],
        CLAUDE_SONNET_5_5: [None, None, None, None, 2.98],
    },
    'Tax Agent Bench v1': {
        GEMINI_4_NEON: [None, None, None, 4.95, None],
        GPT_6_ASTRA: [None, None, None, None, 5.8],
        GPT_6_2_ASTRA: [None, None, None, None, 7.9],
        GPT_6_1_SOL: [None, None, None, None, 1.32],
        GPT_6_2_SOL: [None, None, None, None, 2.4],
        CLAUDE_FABLE_5_2: [None, None, 3.31, None, None],
        CLAUDE_OPUS_5_5: [None, None, None, None, 14.4],
        CLAUDE_SONNET_5_5: [None, None, None, None, 8.73],
        GEMINI_4_CARBON: [None, None, 6.34, None, None],
        GEMINI_4_HYDROGEN: [None, None, None, 3.87, None],
    },
    'Tax Agent Bench v1 (Vals reasoning study)': {
        GPT_6_ASTRA: [1.21, None, 2.82, None, 5.55],
        CLAUDE_OPUS_5_5: [0.0891, None, 0.996, None, 14.6],
        GPT_6_2_ASTRA: [0.534, 1.04, 2.63, 3.91, 8.03],
        CLAUDE_FABLE_5_2: [1.05, None, 3.4, 6.75, 21.1],
    },
    'Vibe Code Bench v1.1 (Vals reasoning study)': {
        GPT_6_ASTRA: [8.55, None, 16.8, None, 34.0],
        CLAUDE_OPUS_5_5: [2.36, None, 9.14, None, 36.4],
        GPT_6_2_ASTRA: [1.3, 3.22, 4.9, 5.83, 7.73],
        CLAUDE_FABLE_5_2: [6.86, None, 21.3, None, None],
    },
    'BioMysteryBench v1': {
        GEMINI_4_NEON: [None, None, None, 4.41, None],
        GPT_6_ASTRA: [None, None, None, None, 1.72],
        GPT_6_2_ASTRA: [None, None, None, None, 1.49],
        GPT_6_1_SOL: [None, None, None, None, 0.372],
        GPT_6_2_SOL: [None, None, None, None, 0.338],
        CLAUDE_FABLE_5_2: [None, None, 1.68, None, None],
        CLAUDE_OPUS_5_5: [None, None, None, None, 2.95],
        CLAUDE_SONNET_5_5: [None, None, None, None, 2.95],
    },
    'HLAB-Vals v1.1': {
        GEMINI_4_NEON: [None, None, None, 5.97, None],
        GPT_6_ASTRA: [None, None, None, None, 25.5],
        GPT_6_2_ASTRA: [None, None, None, None, 7.33],
        GPT_6_1_SOL: [None, None, None, None, 3.54],
        GPT_6_2_SOL: [None, None, None, None, 2.25],
        CLAUDE_FABLE_5_2: [None, None, 19.4, None, None],
        CLAUDE_OPUS_5_5: [None, None, None, None, 21.8],
        CLAUDE_SONNET_5_5: [None, None, None, None, 17.7],
        GEMINI_4_CARBON: [None, None, 6.52, None, None],
        GEMINI_4_HYDROGEN: [None, None, None, 3.28, None],
    },
    'HLAB-Vals v1.1 (Vals reasoning study)': {
        GPT_6_ASTRA: [4.14, None, 11.6, None, 23.8],
        CLAUDE_OPUS_5_5: [4.03, None, 8.13, None, 22.2],
        GPT_6_2_ASTRA: [1.17, 2.34, 3.91, 4.77, 7.31],
        CLAUDE_FABLE_5_2: [11.1, None, 19.6, None, 44.9],
    },
    'Terminal-Bench 4.0 (Vals)': {
        GEMINI_4_NEON: [None, None, None, 6.42, None],
        GPT_6_ASTRA: [None, None, None, None, 9.58],
        GPT_6_2_ASTRA: [None, None, None, None, 4.69],
        GPT_6_1_SOL: [None, None, None, None, 1.72],
        GPT_6_2_SOL: [None, None, None, None, 1.13],
        CLAUDE_FABLE_5_2: [None, None, 14.6, None, None],
        CLAUDE_OPUS_5_5: [None, None, None, None, 12.0],
        CLAUDE_SONNET_5_5: [None, None, None, None, 10.8],
        GEMINI_4_CARBON: [None, None, 7.45, None, None],
        GEMINI_4_HYDROGEN: [None, None, None, 7.56, None],
    },
    'Terminal-Bench 4.0 (Vals) (Vals reasoning study)': {
        GPT_6_ASTRA: [7.49, None, 5.87, None, 8.98],
        CLAUDE_OPUS_5_5: [2.59, None, 4.7, None, 12.6],
        GPT_6_2_ASTRA: [1.48, 1.35, 1.98, 2.33, 3.72],
        CLAUDE_FABLE_5_2: [5.17, None, 13.6, 19.1, 29.5],
    },
    'Terminal-Bench Science 0.1 (Vals)': {
        GEMINI_4_NEON: [None, None, None, 13.7, None],
        GPT_6_ASTRA: [None, None, None, None, 20.8],
        GPT_6_2_ASTRA: [None, None, None, None, 11.1],
        GPT_6_1_SOL: [None, None, None, None, 3.44],
        GPT_6_2_SOL: [None, None, None, None, 2.53],
        CLAUDE_FABLE_5_2: [None, None, 23.1, None, None],
        CLAUDE_OPUS_5_5: [None, None, None, None, 19.1],
        CLAUDE_SONNET_5_5: [None, None, None, None, 19.6],
    },
    'Terminal-Bench 4.1 (provider agents)': {
        CLAUDE_OPUS_5_5: [None, None, None, None, 14.3],
        CLAUDE_FABLE_5_2: [None, None, None, None, 50.0],
        GEMINI_4_CARBON: [None, None, 4.12, None, None],
        CLAUDE_SONNET_5_5: [None, None, None, None, 22.2],
        GPT_6_2_ASTRA: [None, None, None, None, 4.27],
        GPT_6_2_SOL: [None, None, None, None, 1.06],
        GPT_6_1_SOL: [None, None, None, None, 1.92],
        GPT_6_ASTRA: [4.72, 5.8, 6.88, 7.12, 9.9],
        GEMINI_4_HYDROGEN: [None, None, 2.38, None, None],
    },
    'FrontierCode 2.0 (Cognition)': {
        CLAUDE_FABLE_5_2: [2.62, 3.1, 8.4, 17.7, 55.9],
        GPT_6_ASTRA: [2.44, 3.49, 4.28, 4.54, 6.68],
        GPT_6_1_SOL: [0.341, 0.492, 0.647, 0.695, 1.03],
        GPT_6_2_ASTRA: [1.42, 2.47, 3.95, 4.29, 5.97],
        GPT_6_2_SOL: [0.402, 0.685, 0.876, 0.98, 1.29],
        GEMINI_4_CARBON: [7.72, 4.49, 5.06, None, None],
        GEMINI_4_HYDROGEN: [0.353, 0.901, 2.4, 4.95, None],
        GEMINI_4_NEON: [0.959, 2.17, 4.38, 7.67, None],
        CLAUDE_OPUS_5_5: [0.746, 1.7, 2.42, 5.18, 12.8],
        CLAUDE_SONNET_5_5: [0.369, 0.482, 1.07, 3.31, 19.9],
    },
    'AutomationBench 1.0.6 (Zapier)': {
        GEMINI_4_NEON: [0.4, 0.58, 0.88, 1.69, None],
        GEMINI_4_CARBON: [1.02, 1.65, 2.12, None, None],
        GPT_6_2_ASTRA: [0.44, 0.55, 0.67, 0.7, 0.83],
        CLAUDE_FABLE_5_2: [1.3, 1.35, 1.69, 2.29, 4.64],
        GEMINI_4_HYDROGEN: [0.18, 0.41, 0.82, None, None],
        CLAUDE_SONNET_5_5: [0.28, 0.31, 0.36, 0.48, 1.14],
        CLAUDE_OPUS_5_5: [0.51, 0.65, 0.71, 0.89, 1.44],
        GPT_6_ASTRA: [1.08, 1.27, 1.44, 1.5, 1.73],
        GPT_6_2_SOL: [0.13, 0.18, 0.21, 0.23, 0.27],
    },
    "Agents' Last Exam v1.1 (public + Google)": {
        GPT_6_2_ASTRA: [0.521, 1.14, 2.17, 3.05, 4.68],
        GEMINI_4_CARBON: [None, None, 4.6, None, None],
        GPT_6_ASTRA: [5.4, 6.21, 6.87, 7.56, 8.99],
        GPT_6_2_SOL: [0.286, 0.609, 0.733, 0.912, 1.39],
        CLAUDE_FABLE_5_2: [None, None, None, None, 60.1],
        CLAUDE_OPUS_5_5: [None, None, None, None, 17.6],
        GEMINI_4_HYDROGEN: [0.363, 0.837, 1.97, 4.3, None],
    },
    'Terminal-Bench Science 0.1 (public board)': {
        GPT_6_ASTRA: [None, None, None, None, 23.8],
        CLAUDE_OPUS_5_5: [None, None, None, None, 23.2],
    },
    'CWE-bench v2 (250 tasks)': {
        CLAUDE_FABLE_5_2: [None, None, 7.85, None, None],
        GEMINI_4_NEON: [None, None, 6.52, None, None],
        GEMINI_4_HYDROGEN: [None, None, 2.63, None, None],
        GEMINI_4_CARBON: [None, None, 4.27, None, None],
        CLAUDE_OPUS_5_5: [None, None, 1.85, None, None],
        GPT_6_2_ASTRA: [None, None, 4.32, None, None],
        GPT_6_2_SOL: [None, None, 0.81, None, None],
        GPT_6_ASTRA: [None, None, 3.87, None, None],
        CLAUDE_SONNET_5_5: [None, None, 0.58, None, None],
    },
    'CursorBench 4.1': {
        GEMINI_4_NEON: [1.26, 3.07, 6.54, 10.67, None],
        GEMINI_4_CARBON: [8.64, 7.22, 8.52, None, None],
        CLAUDE_FABLE_5_2: [4.26, 5.01, 10.51, 17.84, 48.11],
        CLAUDE_OPUS_5_5: [1.43, 2.85, 3.87, 6.54, 11.88],
        GEMINI_4_HYDROGEN: [0.28, 1.28, 4.57, 8.09, None],
        CLAUDE_SONNET_5_5: [0.44, 0.63, 1.41, 3.13, 8.63],
    },
    'DeepSWE v1.1': {
        MAI_CODE_2: [None, None, None, None, 0.618],
    },
    'Extended NYT Connections (940)': {
        GEMINI_4_NEON: [None, None, 0.0708, None, None],
        GEMINI_4_CARBON: [None, None, 0.0939, None, None],
        GPT_6_ASTRA: [None, None, 0.02807, None, None],
        GPT_6_2_ASTRA: [None, None, 0.01462, None, None],
        GPT_6_1_SOL: [None, None, 0.00686, None, None],
        GPT_6_2_SOL: [None, None, 0.00507, None, None],
    },
    "Humanity's Last Exam": {
        GPT_6_ASTRA: [0.0389, 0.101, 0.162, 0.253, 0.378],
        GPT_6_1_SOL: [0.00731, 0.0126, 0.0266, 0.0428, 0.0776],
        CLAUDE_OPUS_5_5: [0.0286, 0.0619, 0.104, 0.241, 0.718],
        CLAUDE_SONNET_5_5: [0.0128, 0.0232, 0.0473, 0.118, 0.544],
    },
    "CritPt v1": {
        GPT_6_ASTRA: [0.145, 0.285, 0.434, 0.798, 1.17],
        GPT_6_1_SOL: [0.0272, 0.0395, 0.0757, 0.119, 0.242],
        CLAUDE_OPUS_5_5: [0.124, 0.345, 0.53, 1.17, 2.19],
        CLAUDE_SONNET_5_5: [0.0862, 0.149, 0.281, 0.65, 1.89],
    },
    "Vibe Code Bench v1.1": {
        GEMINI_4_NEON: [None, None, None, 6.76, None],
        CLAUDE_FABLE_5_2: [None, None, 22.13, None, None],
        CLAUDE_SONNET_5_5: [None, None, None, None, 19.73],
        CLAUDE_OPUS_5_5: [None, None, None, None, 35.77],
        GPT_6_2_ASTRA: [None, None, None, None, 7.92],
        GPT_6_ASTRA: [None, None, None, None, 38.51],
        GEMINI_4_CARBON: [None, None, 8.25, None, None],
        GPT_6_1_SOL: [None, None, None, None, 6.23],
        GEMINI_4_HYDROGEN: [None, None, None, 4.55, None],
        GPT_6_2_SOL: [None, None, None, None, 3.23],
    },
    "Vals Index": {
        GEMINI_4_NEON: [None, None, None, 7.4, None],
        CLAUDE_FABLE_5_2: [None, None, 17.94, None, None],
        CLAUDE_SONNET_5_5: [None, None, None, None, 16.18],
        GEMINI_4_CARBON: [None, None, 10.51, None, None],
        CLAUDE_OPUS_5_5: [None, None, None, None, 24.77],
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
        GEMINI_4_NEON: [830.0, 1870.0, 3690.0, 7790.0, None],
        GPT_6_ASTRA: [1650.0, 2640.0, 3200.0, 3750.0, 5660.0],
        GPT_6_1_SOL: [238.0, 389.0, 573.0, 718.0, 1120.0],
        CLAUDE_FABLE_5_2: [2860.0, 3360.0, 7110.0, 11700.0, 22200.0],
        CLAUDE_OPUS_5_5: [980.0, 2030.0, 2720.0, 4770.0, 8910.0],
        CLAUDE_SONNET_5_5: [499.0, 679.0, 1270.0, 2900.0, 7980.0],
        GEMINI_4_CARBON: [4050.0, 4000.0, 5330.0, None, None],
        GPT_6_2_ASTRA: [794.0, 1460.0, 2010.0, 2480.0, 4530.0],
        GPT_6_2_SOL: [224.0, 405.0, 553.0, 698.0, 1110.0],
        GEMINI_4_HYDROGEN: [332.0, 804.0, 1770.0, 4090.0, None],
    },
    "HLE-Diamond": {
        GEMINI_4_NEON: [0.0814, 0.28, 0.742, 1.95, None],
        GPT_6_ASTRA: [0.05, 0.12, 0.257, 0.37, 0.551],
        GPT_6_1_SOL: [0.00863, 0.0185, 0.0433, 0.0663, 0.109],
        CLAUDE_FABLE_5_2: [0.128, 0.183, 0.464, 0.876, 1.73],
        CLAUDE_OPUS_5_5: [0.0351, 0.13, 0.194, 0.47, 1.2],
        CLAUDE_SONNET_5_5: [0.015, 0.0327, 0.107, 0.246, 0.804],
        GEMINI_4_CARBON: [0.343, 0.393, 0.814, None, None],
        GPT_6_2_ASTRA: [0.0178, 0.0433, 0.147, 0.234, 0.657],
        GPT_6_2_SOL: [0.00451, 0.0187, 0.0422, 0.076, 0.149],
        GEMINI_4_HYDROGEN: [0.026, 0.144, 0.373, 1.29, None],
    },
    "CritPt v2": {
        GEMINI_4_NEON: [0.359, 1.05, 2.06, 3.46, None],
        GPT_6_ASTRA: [0.237, 0.407, 0.714, 0.849, 1.14],
        GPT_6_1_SOL: [0.0433, 0.0714, 0.134, 0.167, 0.23],
        CLAUDE_FABLE_5_2: [0.313, 0.367, 1.05, 2.47, 6.35],
        CLAUDE_OPUS_5_5: [0.119, 0.251, 0.384, 0.966, 2.58],
        CLAUDE_SONNET_5_5: [0.0731, 0.0926, 0.181, 0.448, 1.93],
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
        GEMINI_4_CARBON: [0.0985, 0.375, 0.684, None, None],
        GPT_6_2_ASTRA: [0.275, 0.309, 0.408, 0.5, 0.97],
        GPT_6_2_SOL: [0.0758, 0.103, 0.133, 0.174, 0.261],
    },
    "AA-Omniscience Index": {
        GEMINI_4_NEON: [0.008, 0.0189, 0.0469, 0.395, None],
        GPT_6_ASTRA: [0.00697, 0.0109, 0.028, 0.0518, 0.0988],
        GPT_6_1_SOL: [0.00149, 0.00215, 0.00493, 0.00918, 0.0183],
        CLAUDE_FABLE_5_2: [0.0138, 0.0153, 0.0196, 0.0326, 0.219],
        CLAUDE_OPUS_5_5: [0.00627, 0.00824, 0.00931, 0.0148, 0.187],
        CLAUDE_SONNET_5_5: [0.00291, 0.00312, 0.00567, 0.00883, 0.152],
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
    },
    "AA-Briefcase": {
        GEMINI_4_NEON: [0.833, 2.17, 4.23, 6.69, None],
        GPT_6_ASTRA: [1.44, 3.94, 4.76, 6.56, 9.5],
        GPT_6_1_SOL: [0.177, 0.464, 0.837, 1.04, 2.31],
        CLAUDE_FABLE_5_2: [5.62, 6.84, 15.5, 28.6, 59.4],
        CLAUDE_OPUS_5_5: [1.15, 4.4, 6.27, 12.3, 21.0],
        CLAUDE_SONNET_5_5: [0.802, 1.39, 3.27, 6.98, 20.5],
        GEMINI_4_CARBON: [5.33, 5.06, 5.85, None, None],
        GPT_6_2_ASTRA: [0.42, 1.26, 2.79, 3.54, 5.49],
        GPT_6_2_SOL: [0.181, 0.525, 0.793, 1.01, 1.57],
        GEMINI_4_HYDROGEN: [0.21, 0.651, 1.73, 3.19, None],
    },
    "AutomationBench-AA": {
        GEMINI_4_NEON: [0.407, 0.601, 0.936, 1.45, None],
        GPT_6_ASTRA: [0.999, 1.18, 1.3, 1.41, 1.6],
        GPT_6_1_SOL: [0.159, 0.196, 0.226, 0.251, 0.297],
        CLAUDE_FABLE_5_2: [1.28, 1.33, 1.69, 2.27, 4.45],
        CLAUDE_OPUS_5_5: [0.493, 0.638, 0.699, 0.878, 1.43],
        CLAUDE_SONNET_5_5: [0.241, 0.262, 0.313, 0.422, 1.03],
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
    },
    "GDP.pdf": {
        GEMINI_4_NEON: [0.32, 0.372, 0.466, 0.875, None],
        GPT_6_ASTRA: [1.7, 1.72, 1.79, 1.91, 2.08],
        GPT_6_1_SOL: [0.334, 0.337, 0.349, 0.368, 0.42],
        CLAUDE_FABLE_5_2: [1.53, 1.56, 1.64, 1.85, 2.52],
        CLAUDE_OPUS_5_5: [0.764, 0.795, 0.825, 0.964, 1.55],
        CLAUDE_SONNET_5_5: [0.372, 0.381, 0.409, 0.46, 0.794],
        GEMINI_4_CARBON: [0.191, 0.24, 0.424, None, None],
        GPT_6_2_ASTRA: [1.32, 1.33, 1.36, 1.4, 1.67],
        GPT_6_2_SOL: [0.331, 0.334, 0.341, 0.359, 0.396],
        GEMINI_4_HYDROGEN: [0.153, 0.174, 0.201, 0.437, None],
    },
    "AA Index coding category": {
        GEMINI_4_NEON: [1.08, 2.62, 4.92, 7.87, None],
        GPT_6_ASTRA: [1.7, 3.45, 3.88, 4.77, 7.32],
        GPT_6_1_SOL: [0.274, 0.492, 0.709, 0.832, 1.41],
        CLAUDE_FABLE_5_2: [3.01, 3.71, 11.2, 21.2, 38.7],
        CLAUDE_OPUS_5_5: [1.21, 2.64, 3.54, 7.41, 13.3],
        CLAUDE_SONNET_5_5: [0.664, 0.825, 1.33, 4.06, 12.0],
        GEMINI_4_CARBON: [8.5, 6.96, 8.17, None, None],
        GPT_6_2_ASTRA: [0.803, 1.85, 2.85, 3.4, 5.38],
        GPT_6_2_SOL: [0.274, 0.546, 0.703, 0.854, 1.3],
        GEMINI_4_HYDROGEN: [0.49, 1.21, 2.67, 4.14, None],
    },
    "Terminal-Bench 4.0": {
        GEMINI_4_NEON: [1.28, 2.92, 4.92, 6.7, None],
        GPT_6_ASTRA: [2.25, 4.43, 4.05, 5.86, 8.5],
        GPT_6_1_SOL: [0.383, 0.614, 0.828, 1.03, 1.82],
        CLAUDE_FABLE_5_2: [4.34, 5.25, 13.5, 20.8, 31.6],
        CLAUDE_OPUS_5_5: [2.08, 4.04, 5.12, 8.78, 13.1],
        CLAUDE_SONNET_5_5: [1.28, 1.58, 2.19, 6.08, 12.6],
        GEMINI_4_CARBON: [6.05, 6.24, 7.11, None, None],
        GPT_6_2_ASTRA: [0.795, 1.75, 2.5, 2.88, 4.66],
        GPT_6_2_SOL: [0.35, 0.677, 0.771, 0.934, 1.29],
        GEMINI_4_HYDROGEN: [0.526, 1.58, 2.8, 3.66, None],
    },
    "FrontierCode-AA 2.0": {
        GEMINI_4_NEON: [0.949, 2.42, 4.91, 8.65, None],
        GPT_6_ASTRA: [1.34, 2.8, 3.77, 4.04, 6.54],
        GPT_6_1_SOL: [0.201, 0.411, 0.63, 0.703, 1.13],
        CLAUDE_FABLE_5_2: [2.12, 2.69, 9.64, 21.4, 43.4],
        CLAUDE_OPUS_5_5: [0.627, 1.71, 2.49, 6.49, 13.5],
        CLAUDE_SONNET_5_5: [0.25, 0.324, 0.76, 2.71, 11.6],
        GEMINI_4_CARBON: [10.1, 7.44, 8.88, None, None],
        GPT_6_2_ASTRA: [0.808, 1.91, 3.08, 3.75, 5.87],
        GPT_6_2_SOL: [0.224, 0.458, 0.658, 0.801, 1.3],
        GEMINI_4_HYDROGEN: [0.467, 0.962, 2.58, 4.47, None],
    },
    "Terminal-Bench Science 0.1": {
        GEMINI_4_NEON: [1.79, 4.93, 10.1, 18.4, None],
        GPT_6_ASTRA: [4.12, 7.2, 8.66, 7.91, 17.5],
        GPT_6_1_SOL: [0.242, 0.872, 1.61, 2.3, 3.34],
        CLAUDE_FABLE_5_2: [8.78, 11.0, 24.3, 31.4, 45.2],
        CLAUDE_OPUS_5_5: [2.81, 6.8, 10.0, 14.1, 20.0],
        CLAUDE_SONNET_5_5: [1.23, 2.14, 4.98, 12.8, 23.8],
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
COST_UNITS = {"Code Migration v1.1 (Vals Index subset)": "US$ per test, log scale",
              "Code Migration v1.1 (Vals full test set)": "US$ per test, log scale",
              'Vals Index': "US$ per test, log scale",
              'Vals Index (Vals reasoning study)': "US$ per test, log scale",
              'Vals Finance Index v1': "US$ per test, log scale",
              'Vals Legal Index v1': "US$ per test, log scale",
              'Vals Science Index v1 (Vals)': "US$ per test, log scale",
              'EMB v1.1': "US$ per test, log scale",
              'EMB v1.1 (Vals reasoning study)': "US$ per test, log scale",
              'Finance Agent v2.1': "US$ per test, log scale",
              'Finance Agent v2.1 (Vals reasoning study)': "US$ per test, log scale",
              'Legal Research Bench v1': "US$ per test, log scale",
              'Legal Research Bench v1 (Vals reasoning study)': "US$ per test, log scale",
              'MysteryMechanism v1': "US$ per test, log scale",
              'Tax Agent Bench v1': "US$ per test, log scale",
              'Tax Agent Bench v1 (Vals reasoning study)': "US$ per test, log scale",
              'Vibe Code Bench v1.1': "US$ per test, log scale",
              'Vibe Code Bench v1.1 (Vals reasoning study)': "US$ per test, log scale",
              'BioMysteryBench v1': "US$ per test, log scale",
              'HLAB-Vals v1.1': "US$ per test, log scale",
              'HLAB-Vals v1.1 (Vals reasoning study)': "US$ per test, log scale",
              'Terminal-Bench 4.0 (Vals)': "US$ per test, log scale",
              'Terminal-Bench 4.0 (Vals) (Vals reasoning study)': "US$ per test, log scale",
              'Terminal-Bench Science 0.1 (Vals)': "US$ per test, log scale",
              "Extended NYT Connections (940)": "Estimated US$ per puzzle, standard prices, log scale",
              "AA Intelligence Index": "US$ to run the whole index, log scale",
              "Vals Index": "US$ per test, log scale", "Vibe Code Bench v1.1": "US$ per test, log scale"}
DEFAULT_COST_UNIT = "US$ per task, log scale"

TITLE = "AI scores"
TAGLINE = "Every published score, by thinking level and price."
FILTER_LEVELS = [*EFFORT_LEVELS, "not-stated"]

FOOTNOTES = {
    "Aggregates": "Scores checked on 19 November 2026. Every published effort level is shown; gaps mean no score, not zero. "
                  "The Claude models use adaptive reasoning; Carbon stops at high, Hydrogen at xhigh. "
                  "AA Intelligence Index is v5.0.1; its costs are for the whole index, while other cost axes are US dollars per task. "
                  "AA publishes weighted task costs: we divide by its benchmark weights to recover per-task costs. "
                  "Carbon's AA prices use Google's introductory US$2/US$10 per million tokens; Hydrogen is US$1.50/US$7.50. "
                  "Missing costs do not remove scores: the effort chart remains available. "
                  "System-card results without a stated effort are bars marked \u201cnot stated\u201d, never assigned to max. "
                  "No benchmark is omitted just for sparse coverage. Cost comparisons use the visible point estimates. "
                  "They do not account for statistical uncertainty or differences in harnesses. "
                  "Vals headline scores retain its published fallback policy, including other models’ answers for some Claude failures; "
                  "the separate reasoning studies use fixed approximately half-task subsets, not full-board runs. "
                  "Exact nonstandard effort labels remain on bars: none, between tools and highest (level not stated) are grouped "
                  "under Not stated; highest/high mixed is grouped under max. These filter mappings are judgment calls, not equivalent settings.",
    "Intelligence & knowledge": "ARC Prize has no Sonnet max run. Agents' Last Exam and LifeVal are OpenAI launch comparisons, "
                                "labeled separately from AA runs. On Agents' Last Exam, Fable excludes nine fallback tasks, "
                                "so it is not a perfectly matched-task comparison. The public+Google ALE chart is a separate provider-agent run. "
                                "Google’s MKA 52.7 and Science 68.0 model labels conflict with the native boards; native attributions are used, "
                                "and the conflicting Google-copy points are omitted.",
    "Professional work": "GDPval-AA and AA-Briefcase are relative Elo ratings, refreshed together. "
                         "AutomationBench-AA and MKA are AA's runs. AutomationBench 1.0.6 and GDPval v2 are OpenAI launch "
                         "comparisons, so they are not the same runs as AA's. Zapier’s native 1.0.6 board is separate again. "
                         "Surge GDP.pdf v1.1 is agentic, HANDBOOK v1.1 changes grading, and their unreported current costs stay absent. "
                         "Vals HLAB is not Harvey LAB-AA.",
    "Science & engineering": "GPQA Diamond from AA and from OpenAI's system card stay separate charts. "
                             "Vals Science Index and BenchCAD are OpenAI launch comparisons. "
                             "Neither GPT-6.2 model has a published SciCode score in the checked sources. Native provider-agent Science runs "
                             "(three trials), Google’s vision-enabled mini-SWE run (five attempts), Vals’ single-run Mini-SWE, and AA stay separate. "
                             "Riemann v1.1 corrects four answer keys.",
    "Health": "HealthBench Professional replaces the older HealthBench; AA and OpenAI runs stay separate. "
              "OpenAI's health results state no effort, except MentalHealthBench, which says max.",
    "Coding & security": "FrontierCode 2.0 replaces the 1.1 Main chart. FrontierCode-AA 2.0 uses AA's harness; the other 2.0 chart "
                         "is OpenAI's published comparison and must not be treated as the same run. Neither GPT-6.2 model has a "
                         "published DeepSWE or SWE-Bench Pro score in the checked sources. DeepSWE's GPT points are OpenAI's. "
                         "SWE-Bench Pro bars are each lab's own harness, so compare cautiously. "
                         "The coding category uses FrontierCode-AA and Terminal-Bench 4.0 with 15:10 weights, including their costs. "
                         "SecureSWE, PatchBench and ExploitBench are internal cyber evaluations with safeguards disabled, not "
                         "ordinary deployment results. CursorBench 4.1 supersedes 4.0; older versions are available through the older-scores line. "
                         "MAI Code 2’s DeepSWE and historical Terminal-Bench use Copilot CLI 1.0.102; its old FrontierCode point is AA’s. "
                         "MAI costs use 50% promotional pricing. Older versions have different tasks or scoring, not comparable percentages. "
                         "Terminal-Bench 4.1’s Neon point is AA via Google, not a native-board entry. SEC 260505 has 183 tasks, not the newer 344-task split. "
                         "Code Migration’s 60-task Vals Index subset and 130-task full set are separate; both weight CLI:COBOL 75:25. "
                         "AutoBax highest/high mixed reruns context-limited tasks at high; unspecified highest is not max. "
                         "ExploitGym charts separate time/token budgets; token-budgeted counts are approximate board-derived counts, and no Neon result is available.",
    "Machine-learning research": "These are OpenAI system-card results with no stated effort. "
                                 "NanoGPT v5 omits older Astra's v4 score rather than mixing versions.",
    "Multimodal tasks": "AA-3D is human-preference Elo, not percent accuracy; its reported effort is not specified. "
                        "Surge Chartography v1.1 is agentic; Google’s no-tools Chartography run stays separate.",
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
AXES_RIGHT = 1.15
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
        "axes.edgecolor": BASELINE.value,
        "xtick.color": TEXT_MUTED.value,
        "ytick.color": TEXT_MUTED.value,
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


def filter_level(level: str) -> str:
    """Keep exact reported labels while grouping nonstandard settings under existing filter chips.

    >>> [filter_level(level) for level in ("high", "none", "between tools", "highest/high mixed")]
    ['high', 'not-stated', 'not-stated', 'max']
    """
    return slugify(level) if level in [*EFFORT_LEVELS, "not stated"] else {
        "none": "not-stated", "between tools": "not-stated",
        "highest (level not stated)": "not-stated", "highest/high mixed": "max",
    }[level]


def at_level(gid: str, level: str) -> str:
    """Tag a rendered point or bar with its reported thinking level.

    >>> at_level("marker__gpt-6-astra", "high")
    'marker__gpt-6-astra__level-high'
    """
    return f"{gid}__level-{filter_level(level)}"


def element_models(artist: Artist) -> set[str]:
    return {part for part in artist.get_gid().split("__")[1:] if not part.startswith("level-")}


MEETING_LINE = "meeting-line"

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

LABEL_HALO = {"boxstyle": "round,pad=0.12", "facecolor": SURFACE.value, "edgecolor": "none"}
POINT_LABEL_STYLE = {"fontsize": LABEL_FONT_SIZE, "fontweight": "medium", "color": TEXT_PRIMARY.value, "zorder": 5,
                     "bbox": LABEL_HALO}
DIM_LABEL_STYLE = {"fontsize": NAME_FONT_SIZE, "family": NAME_FONT_FAMILY, "color": TEXT_MUTED.value, "zorder": 5,
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
        return artist not in own_parts and gid not in ignored_ids and not gid.startswith(MEETING_LINE) \
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
    leader = {"arrowprops": {"arrowstyle": "-", "color": BASELINE.value, "linewidth": 0.6, "shrinkA": 1, "shrinkB": 4}} \
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
        axes.plot([first_index, second_index], [height, height], color=TEXT_MUTED.value, linewidth=0.9,
                  linestyle=(0, (2.5, 2.5)), alpha=0.8, zorder=2.5, gid=element_id(MEETING_LINE, first, second))
        for model, index in meeting:
            if index in labeled_levels(metric.scores[model]):
                continue
            score = metric.scores[model][index]
            placements = PLACEMENT_ORDERS[("meeting", away_is_above(metric, model, index, [first, second]))] + COST_END_PLACEMENTS
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
            axes.plot([index + 0.1, label_x - 0.06], [score, label_y], color=BASELINE.value, linewidth=0.6,
                      solid_capstyle="round", zorder=2, gid=element_id("leader", model))
        axes.text(label_x, label_y, metric.label(score), color=TEXT_PRIMARY.value, fontsize=LABEL_FONT_SIZE,
                  fontweight="medium", va="center", ha="left", gid=element_id("end", model))
    renderer = axes.figure.canvas.get_renderer()
    widest_end = max(text.get_window_extent(renderer).x1 for text in axes.texts)
    name_x = from_display((widest_end + NAME_GAP_POINTS * axes.figure.dpi / 72, 0))[0]
    for (model, _, _), label_y in zip(ends, label_ys):
        axes.text(name_x, label_y, model.name, color=TEXT_MUTED.value, fontsize=NAME_FONT_SIZE, family=NAME_FONT_FAMILY,
                  va="center", ha="left", gid=element_id("name", model))


def draw_series(axes: Axes, metric: Metric, model: Model, points: list[tuple[int, float, float]]) -> None:
    """Draw one model's line and markers through (level, x, score) points, hollow where AA estimated the score."""
    axes.plot([x for _, x, _ in points], [score for _, _, score in points], color=model.color.value,
              linewidth=LINE_WIDTH, solid_joinstyle="round", solid_capstyle="round", zorder=3,
              gid=element_id("series", model))
    for index, x, score in points:
        is_estimated = (model, EFFORT_LEVELS[index]) in metric.estimated
        axes.plot(x, score, marker="o", markersize=MARKER_SIZE, linestyle="none",
                  markerfacecolor=SURFACE.value if is_estimated else model.color.value,
                  markeredgecolor=model.color.value if is_estimated else SURFACE.value,
                  markeredgewidth=MARKER_RING, zorder=4,
                  gid=at_level(element_id("marker", model), EFFORT_LEVELS[index]))


def style_axes(axes: Axes, metric: Metric) -> None:
    axes.set_ylim(*metric.y_range)
    axes.yaxis.set_gid("score-axis__ticks")
    axes.yaxis.set_major_locator(matplotlib.ticker.MultipleLocator(metric.tick_step))
    axes.grid(axis="y", color=GRIDLINE.value, linewidth=0.7)
    axes.set_axisbelow(True)
    for side in ("top", "right", "left"):
        axes.spines[side].set_visible(False)
    axes.spines["bottom"].set_color(BASELINE.value)
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

    >>> cost_points(CURVES[0], GPT_6_1_SOL)[0]
    (0, 238.0, 34.8)
    """
    costs = metric.costs.get(model, [None] * len(EFFORT_LEVELS))
    return [(index, cost, score) for index, (score, cost) in enumerate(zip(metric.scores[model], costs))
            if score is not None and cost is not None]


def cost_label(value: float) -> str:
    """
    >>> [cost_label(value) for value in (0.002, 0.05, 1.5, 20, 1000, 12500)]
    ['$0.002', '$0.05', '$1.5', '$20', '$1k', '$12.5k']
    """
    return f"${value / 1000:.3g}k" if value >= 1000 else f"${value:.3g}"


def draw_cost_panel(axes: Axes, metric: Metric) -> None:
    """Plot score against measured cost on a log scale, with optional end labels where there is room.

    The browser adds dominance links for the selected models and levels.
    """
    models = [model for model in metric.models if cost_points(metric, model)]
    for model in models:
        draw_series(axes, metric, model, cost_points(metric, model))
    style_axes(axes, metric)
    costs = [cost for model in models for _, cost, _ in cost_points(metric, model)]
    decades = math.log10(max(costs) / min(costs))
    axes.set_xscale("log")
    axes.set_xlim(min(costs) / 10 ** (0.12 * decades + 0.1), max(costs) * 10 ** (0.35 * decades + 0.2))
    tick_multiples = (1, 2, 5) if decades <= 1.5 else (1, 3) if decades <= 2.5 else (1,)
    axes.xaxis.set_major_locator(matplotlib.ticker.LogLocator(base=10, subs=tick_multiples))
    axes.xaxis.set_minor_locator(matplotlib.ticker.NullLocator())
    axes.xaxis.set_major_formatter(matplotlib.ticker.FuncFormatter(lambda value, _: cost_label(value)))
    axes.grid(axis="x", color=GRIDLINE.value, linewidth=0.7)
    axes.set_xlabel(metric.cost_unit, fontsize=8.5, color=TEXT_MUTED.value, labelpad=6)
    axes.figure.canvas.draw()
    for model in models:
        index, cost, score = cost_points(metric, model)[-1]
        level = "" if EFFORT_LEVELS[index] == "max" else f" · {EFFORT_LEVELS[index]}"  # most lines end at max
        parts = [value_part(metric, score), (f"{model.name}{level}", DIM_LABEL_STYLE)]
        place_label(axes, metric, (cost, score), parts, COST_END_PLACEMENTS, element_id("end", model), model, models,
                    required=False)


def inline_svg(svg: str) -> str:
    """Make matplotlib's SVG fit inline in the page: no fixed size, theme colors as CSS variables, gids as CSS classes.

    >>> inline_svg('<?xml?>\\n<svg width="9pt" height="9pt" viewBox="0 0 9 9"><g id="end__gpt-6-sol" style="fill: #ffffff"/></svg>')
    '<svg class="chart" viewBox="0 0 9 9"><g class="end m-gpt-6-sol" style="fill: var(--ink-1)"/></svg>'
    """
    svg = svg[svg.index("<svg"):]
    # matplotlib's global "*" rule and metadata would leak into, or bloat, the page.
    svg = re.sub(r"<metadata>.*?</metadata>|<style[^>]*>.*?</style>", "", svg, flags=re.DOTALL)
    svg = re.sub(r' width="[\d.]+pt" height="[\d.]+pt"', ' class="chart"', svg, count=1)
    for color in COLORS:
        svg = svg.replace(color.value, f"var(--{color.variable})")
    svg = re.sub(r'__level-([a-z-]+)"', r'" data-level="\1"', svg)
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
    return (f'<span class="column" data-level="{EFFORT_LEVELS[index]}" style="left:{100 * left / width:.2f}%;width:{100 * (right - left) / width:.2f}%;'
            f'top:{100 * (1 - top / height):.2f}%;height:{100 * (top - bottom) / height:.2f}%">'
            f'{"".join(rings)}<span class="tip {side}"><span class="level">{EFFORT_LEVELS[index]}</span>{"".join(rows)}</span></span>')


def cost_point_html(axes: Axes, metric: Metric, model: Model, index: int, cost: float, score: float) -> str:
    """A hover target on one cost-chart point, with its level, score and cost."""
    width, height = axes.figure.bbox.size
    x, y = axes.transData.transform((cost, score))
    estimated = " <i>est.</i>" if (model, EFFORT_LEVELS[index]) in metric.estimated else ""
    side = "tip-left" if x / width > 0.6 else "tip-right"
    return (f'<span class="cost-point m-{model.slug}" data-level="{EFFORT_LEVELS[index]}" '
            f'style="left:{100 * x / width:.2f}%;top:{100 * (1 - y / height):.2f}%">'
            f'<span class="tip {side}"><span class="level">{EFFORT_LEVELS[index]}</span>'
            f'<span class="row" style="--series: var(--{model.color.variable})"><b>{metric.label(score)}</b>'
            f'{html.escape(model.name)}{estimated}</span><span class="cost">{cost_label(cost)} · {metric.cost_unit.split(",")[0]}</span>'
            '</span></span>')


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
    else:
        draw_panel(axes, metric)
        hover = "".join(level_column_html(axes, metric, index) for index in range(len(EFFORT_LEVELS))
                        if any(metric.scores[model][index] is not None for model in metric.models))
    box = axes.get_position()
    axes_percent = ",".join(f"{100 * value:.3f}" for value in (box.x0, 1 - box.y1, box.width, box.height))
    x_limits = ",".join(f"{value:.12g}" for value in axes.get_xlim())
    attributes = (f' data-metric="{slugify(metric.name)}" data-mode="{mode}" '
                  f'data-axes="{axes_percent}" data-x-limits="{x_limits}"')
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
    return (f'<figure class="panel" data-chart="{slugify(metric.name)}"><figcaption><h3>{html.escape(metric.name)}</h3>'
            f'<p>{html.escape(metric.unit_and_source)}</p>{note}</figcaption>'
            f'{"".join(plot_html(metric, layout, mode) for layout in LAYOUTS for mode in modes)}</figure>')


BAR_ROW_HEIGHT = 0.42
BAR_THICKNESS = 0.56  # of a row
BAR_AXES_LEFT = 1.35  # holds the model names
BAR_AXES_BOTTOM = 0.32


def draw_bars(axes: Axes, metric: ReportedMetric) -> None:
    """One horizontal bar per reported model, top to bottom in model order, labeled with its score and effort level."""
    rows = list(reversed(metric.models))
    for row, model in enumerate(rows):
        score, effort = metric.scores[model]
        axes.barh(row, score, height=BAR_THICKNESS, color=model.color.value, zorder=3,
                  gid=at_level(element_id("bar", model), effort))
        axes.annotate(model.name, (0, row), xytext=(-8, 0), textcoords="offset points", ha="right", va="center",
                      fontsize=LABEL_FONT_SIZE, color=TEXT_PRIMARY.value, annotation_clip=False,
                      gid=at_level(element_id("name", model), effort))
    axes.set_xlim(0, metric.x_max)
    axes.set_ylim(-0.6, len(rows) - 0.4)
    axes.set_yticks([])
    axes.xaxis.set_gid("bar-axis__ticks")
    axes.spines["left"].set_gid("bar-baseline__line")
    axes.xaxis.set_major_locator(matplotlib.ticker.MultipleLocator(metric.tick_step))
    axes.grid(axis="x", color=GRIDLINE.value, linewidth=0.7)
    axes.set_axisbelow(True)
    for side in ("top", "right", "bottom"):
        axes.spines[side].set_visible(False)
    axes.spines["left"].set_color(BASELINE.value)
    axes.tick_params(axis="both", length=0, labelsize=9, pad=5)
    axes.figure.canvas.draw()
    for row, model in enumerate(rows):
        score, effort = metric.scores[model]
        effort_label = f"{effort} · {cost_label(metric.prices[model])}" if model in metric.prices else effort
        for part in annotate_parts(axes, (score, row), [(f"{score:.{metric.decimals}f}", POINT_LABEL_STYLE), (effort_label, DIM_LABEL_STYLE)],
                                   RIGHT, at_level(element_id("end", model), effort)):
            part.set_annotation_clip(False)


def bar_plot_html(metric: ReportedMetric, layout: Layout) -> str:
    width = layout.figure_size[0]
    height = AXES_TOP + BAR_AXES_BOTTOM + BAR_ROW_HEIGHT * len(metric.models)
    plt.rcParams["svg.hashsalt"] = f"{metric.name} {layout.name}"
    figure = plt.figure(figsize=(width, height), dpi=72)
    axes = figure.add_axes((BAR_AXES_LEFT / width, BAR_AXES_BOTTOM / height,
                            1 - (BAR_AXES_LEFT + AXES_RIGHT) / width, 1 - (AXES_TOP + BAR_AXES_BOTTOM) / height))
    draw_bars(axes, metric)
    row_height = axes.transData.transform((0, 1))[1] - axes.transData.transform((0, 0))[1]
    svg = io.StringIO()
    figure.savefig(svg, format="svg", metadata={"Date": None})
    plt.close(figure)
    modes = "effort" if metric.costs else "effort cost"
    return layout_html(f'<div class="plot {layout.name} {modes}" data-row-height="{row_height:.6f}" '
                       f'data-full-height="{height * 72:.6f}">{inline_svg(svg.getvalue())}</div>', layout)


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
    plots = "".join(bar_plot_html(metric, layout) for layout in LAYOUTS)
    if metric.costs:
        plots += "".join(plot_html(reported_cost_metric(metric), layout, "cost") for layout in LAYOUTS)
    return (f'<figure class="panel" data-chart="{slugify(metric.name)}"><figcaption><h3>{html.escape(metric.name)}</h3>'
            f'<p>{html.escape(metric.unit_and_source)}</p></figcaption>'
            f'{plots}</figure>')


def sectioned[Chart: (Metric, ReportedMetric)](kind: type[Chart]) -> Iterator[tuple[str, Chart]]:
    """Each chart of one kind with its section name, in page order."""
    for category, charts in SECTIONS:
        for chart in charts:
            if isinstance(chart, kind):
                yield category, chart


def table_rows() -> Iterator[tuple[str, Metric, Model]]:
    for category, metric in sectioned(Metric):
        for model in metric.models:
            yield category, metric, model


def table_html() -> str:
    head = "".join(f'<th data-level="{level}">{level}</th>' for level in EFFORT_LEVELS)
    rows = []
    for category, metric, model in table_rows():
        is_first = model is metric.models[0]
        cells = "".join(f'<td data-level="{level}">{"" if score is None else metric.label(score)}</td>'
                        for level, score in zip(EFFORT_LEVELS, metric.scores[model]))
        rows.append(f'<tr class="m-{model.slug}{" first" if is_first else ""}">'
                    f'<th scope="row">{html.escape(metric.name) if is_first else ""}</th>'
                    f'<td class="model">{html.escape(model.name)}</td>{cells}</tr>')
        if metric.costs and model in metric.costs:
            costs = "".join(f'<td data-level="{level}">{"" if cost is None else cost_label(cost)}</td>'
                            for level, cost in zip(EFFORT_LEVELS, metric.costs[model]))
            rows.append(f'<tr class="cost-row m-{model.slug}"><th scope="row"></th><td class="model">cost</td>{costs}</tr>')
    reported_rows = [f'<tr class="m-{model.slug}" data-level="{filter_level(effort)}"><th scope="row">{html.escape(metric.name)}</th>'
                     f'<td class="model">{html.escape(model.name)}</td><td>{score:.{metric.decimals}f}</td>'
                     f'<td>{html.escape(effort)}</td><td>{html.escape(metric.unit_and_source)}</td>'
                     f'<td>{cost_label(metric.prices[model]) if model in metric.prices else cost_label(next(cost for cost in metric.costs[model] if cost is not None)) if metric.costs and model in metric.costs else ""}</td></tr>'
                     for metric in REPORTED
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
    """Hide unselected models and levels, and show a meeting only when its two models alone are on."""
    rules = []
    for family in BENCHMARK_VERSIONS.values():
        default = next(version for version in family if version.runners)
        rules.extend(f'body:not(.zoomable) .panel[data-chart="{slugify(name)}"] {{ display: none; }}'
                     for version in family if version is not default for name in version.runners)
    for model in MODELS:
        off = f"body:has(#show-{model.slug}:not(:checked))"
        rules.append(f"{off} .m-{model.slug} {{ display: none; }}")
    for pair in itertools.combinations(MODELS, 2):
        states = "".join(f":has(#show-{model.slug}:{'checked' if model in pair else 'not(:checked)'})" for model in MODELS)
        rules.append(f"body{states} :is(.meeting, .meeting-line)"
                     f"{''.join(f'.m-{model.slug}' for model in pair)} {{ display: inline; }}")
    for level in FILTER_LEVELS:
        rules.append(f'body:has(#level-{level}:not(:checked)) [data-level="{level}"] {{ display: none; }}')
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
:root { color-scheme: dark; $colors }
* { box-sizing: border-box; }
body { margin: 0; background: var(--page); color: var(--ink-1);
  font: 15px/1.45 "Helvetica Neue", system-ui, -apple-system, sans-serif; -webkit-text-size-adjust: 100%; }
.shell { padding: 0 clamp(16px, 2vw, 40px); }
.intro { padding-top: 36px; padding-bottom: 24px; }
h1 { margin: 0; font-size: 30px; line-height: 1.1; letter-spacing: -0.02em; }
.tagline { margin: 8px 0 0; font-size: 17px; color: var(--ink-2); text-wrap: balance; }
.hint { display: none; margin: 12px 0 0; font-size: 13px; color: var(--ink-3); }
.zoomable .hint { display: block; }
.cost-hint, body:has(#x-cost:checked) .effort-hint { display: none; }
body:has(#x-cost:checked) .cost-hint { display: inline; }
.controls { position: sticky; top: 0; z-index: 10; background: var(--page); border-bottom: 1px solid var(--border); }
.controls label, .controls button { cursor: pointer; user-select: none; -webkit-user-select: none; -webkit-tap-highlight-color: transparent; }
.bar { display: flex; align-items: center; gap: 12px; min-height: 64px; }
.filters-button { display: inline-flex; align-items: center; gap: 8px; min-width: 0; height: 42px; padding: 0 14px;
  border: 1px solid var(--baseline); border-radius: 999px; font-weight: 600; transition: background-color .18s ease, transform .12s ease; }
.filters-button svg { flex: none; width: 18px; height: 18px; fill: none; stroke: currentColor; stroke-width: 1.7; stroke-linecap: round; }
.filter-summary { display: none; min-width: 0; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; font-weight: 400; color: var(--ink-3); }
.filter-summary::first-letter { text-transform: uppercase; }
.filter-dot { display: none; width: 7px; height: 7px; border-radius: 50%; background: var(--ink-1); }
.narrowed .filter-dot { display: block; }
.chevron { transition: transform .22s ease; }
body:has(#filters-open:checked) .chevron { transform: rotate(180deg); }
body:has(#filters-open:checked) .filters-button { background: color-mix(in srgb, var(--ink-1) 8%, transparent); }
.segmented { display: inline-flex; flex: none; align-items: center; margin-left: auto; padding: 3px; border-radius: 999px;
  background: color-mix(in srgb, var(--ink-1) 8%, transparent); }
.segmented-caption { display: none; padding: 0 8px 0 10px; font-size: 12px; color: var(--ink-3); }
.segmented label { position: relative; display: inline-flex; align-items: center; height: 36px; padding: 0 14px; border-radius: 999px;
  font-size: 14px; font-weight: 600; color: var(--ink-3); transition: background-color .2s ease, color .2s ease, box-shadow .2s ease, transform .12s ease; }
.segmented label:has(:checked) { background: var(--surface); color: var(--ink-1); box-shadow: 0 1px 4px rgba(0, 0, 0, .25); }
.filters-button:active, .segmented label:active, .chip:active, .quick button:active, .done:active { transform: scale(.96); }
:is(.segmented label, .chip):has(:focus-visible), body:has(#filters-open:focus-visible) .filters-button {
  outline: 2px solid var(--ink-2); outline-offset: 2px; }
@media (min-width: 480px) { .segmented-caption, .filter-summary { display: inline; } .narrowed .filter-dot { display: none; } }
.filter-panel { display: grid; grid-template-rows: 0fr; visibility: hidden; opacity: 0; }
body:has(#filters-open:checked) .filter-panel { grid-template-rows: 1fr; visibility: visible; opacity: 1; }
.zoomable .filter-panel { transition: grid-template-rows .24s ease, opacity .18s ease, visibility 0s linear .24s; }
body.zoomable:has(#filters-open:checked) .filter-panel { transition: grid-template-rows .24s ease, opacity .18s ease; }
.panel-inner { min-height: 0; max-height: calc(100dvh - 65px); overflow-y: auto; overscroll-behavior: contain; }
.panel-inner::after { content: ""; display: block; height: 20px; }
.filter-group + .filter-group { margin-top: 28px; }
.levels, .quick { display: none; }
.zoomable .levels { display: block; }
.zoomable .quick { display: flex; gap: 4px; }
.group-head { display: flex; align-items: center; justify-content: space-between; min-height: 36px; margin: 4px 0 10px; }
.group-title { font-size: 12px; font-weight: 600; letter-spacing: .08em; text-transform: uppercase; color: var(--ink-3); }
.quick button { font: inherit; font-size: 14px; color: var(--ink-2); background: none; border: 0; padding: 8px 10px; border-radius: 8px;
  transition: background-color .15s ease, transform .12s ease; }
.quick button:hover { background: color-mix(in srgb, var(--ink-1) 8%, transparent); }
.chips { display: flex; flex-wrap: wrap; gap: 10px; }
.chip { position: relative; display: inline-flex; align-items: center; gap: 9px; min-height: 44px; padding: 0 14px 0 12px; white-space: nowrap;
  border: 1px solid var(--baseline); border-radius: 12px; font-size: 14px; font-weight: 500; color: var(--ink-3);
  transition: background-color .18s ease, border-color .18s ease, color .18s ease, transform .12s ease; }
.chip:has(:checked) { color: var(--ink-1); border-color: color-mix(in srgb, var(--series) 60%, transparent);
  background: color-mix(in srgb, var(--series) 14%, transparent); }
.tick { display: grid; flex: none; place-items: center; width: 18px; height: 18px; border: 2px solid var(--series); border-radius: 50%;
  transition: background-color .18s ease; }
.chip:has(:checked) .tick { background: var(--series); }
.tick svg { width: 12px; height: 12px; fill: none; stroke: var(--surface); stroke-width: 2.2; stroke-linecap: round; stroke-linejoin: round;
  opacity: 0; transform: scale(.4); transition: opacity .15s ease, transform .22s cubic-bezier(.3, 1.6, .5, 1); }
.chip:has(:checked) .tick svg { opacity: 1; transform: scale(1); }
.done { display: flex; align-items: center; justify-content: center; height: 46px; margin-top: 28px; border-radius: 12px;
  background: var(--ink-1); color: var(--surface); font-weight: 600; transition: transform .12s ease; }
@media (min-width: 960px) {
  .panel-inner { display: grid; grid-template-columns: minmax(0, 1fr) auto; gap: 0 48px; align-items: start; }
  .filter-group + .filter-group { margin-top: 0; }
  .done { display: none; }
}
@media (prefers-reduced-motion: reduce) { .controls *, .filter-panel { transition: none !important; } }
.version-controls { margin-top: 8px; font-size: 12px; color: var(--ink-3); }
.version-controls button { font: inherit; padding: 0; color: inherit; background: none; border: 0; cursor: pointer; }
.old-version { display: inline-block; margin-right: 8px; padding: 1px 6px; border: 1px solid var(--border); border-radius: 4px; font-size: 11px; }
.version-controls .older-versions { display: block; margin-top: 5px; text-align: left; text-decoration: underline dotted; text-underline-offset: 3px; }
.version-controls .version-reset { color: var(--ink-2); text-decoration: underline; text-underline-offset: 3px; }
.panel[data-temporary="true"] { border-style: dashed; }
#benchmark-versions { width: min(420px, calc(100vw - 32px)); max-height: calc(100dvh - 48px); padding: 20px;
  color: var(--ink-1); background: var(--surface); border: 1px solid var(--border); border-radius: 14px; }
#benchmark-versions::backdrop { background: rgba(0, 0, 0, .3); }
#benchmark-versions h3 { margin: 0; font-size: 18px; }
#benchmark-versions p { margin: 8px 0 16px; font-size: 13px; color: var(--ink-3); }
.version-dialog-head { display: flex; justify-content: space-between; align-items: center; gap: 12px; }
.version-dialog-head button { font: 24px/1 system-ui; padding: 0 4px; color: var(--ink-2); background: none; border: 0; cursor: pointer; }
.version-list { display: grid; gap: 8px; }
.version-list button { display: grid; gap: 3px; width: 100%; padding: 12px; text-align: left; font: inherit;
  background: none; color: var(--ink-1); border: 1px solid var(--border); border-radius: 8px; cursor: pointer; }
.version-list button:hover { background: color-mix(in srgb, var(--ink-1) 5%, transparent); }
.version-list button span:last-child { font-size: 12px; color: var(--ink-3); }
.no-cost { display: none; }
body:has(#x-cost:checked) .no-cost { display: block; }
.cost-row { display: none; color: var(--ink-3); }
body:has(#x-cost:checked) .cost-row { display: table-row; }
.toggle { position: absolute; opacity: 0; pointer-events: none; }
h2 { margin: 32px 0 12px; font-size: 13px; letter-spacing: .08em; text-transform: uppercase; color: var(--ink-2); }
.grid { display: grid; grid-template-columns: 1fr; gap: 16px; align-items: start; }
@media (min-width: 960px) { .grid { grid-template-columns: 1fr 1fr; } }
.panel { margin: 0; padding: 16px 16px 8px; background: var(--surface); border: 1px solid var(--border); border-radius: 10px; }
figcaption h3 { margin: 0; font-size: 16px; }
figcaption p { margin: 2px 0 0; font-size: 13px; color: var(--ink-3); }
.plot { position: relative; display: none; }
/* With JavaScript, only the active layout and mode are mounted, so the old charts stay until the new ones replace them. */
.zoomable .panel > .plot { display: block; }
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
.cost-point:not(:hover, .dominance-hover) .tip { display: none; }
.cost-point .tip { top: -8px; }
.cost-point .tip-right { left: calc(100% + 4px); }
.cost-point .tip-left { right: calc(100% + 4px); }
.zoomable .cost-point .tip { position: fixed; inset: 0 auto auto 0; min-width: 0; width: min(300px, calc(100vw - 24px)); white-space: normal; }
.tip .cost { color: var(--ink-3); }
.tip .beaten { margin-top: 4px; padding-top: 4px; border-top: 1px solid var(--border); }
.cost-point:is(:hover, .dominance-hover) { z-index: 4; }
.zoomable .plot[data-mode="cost"] .series { opacity: .35; }
.cost-marker { transform-box: view-box; transition: transform 160ms ease; }
.cost-marker:not(.dominated) { filter: saturate(1.25) brightness(1.15); }
.cost-marker.highlighted { transform: scale(1.3); }
.dominance-link { opacity: .7; stroke: var(--ink-3); stroke-width: 1.2; fill: none; pointer-events: none; }
.dominance-link.highlighted { opacity: 1; }
/* Link hit targets must sit above the point tooltips, even when the endpoints are close together. */
.dominance-hit-layer { position: absolute; inset: 0; width: 100%; height: 100%; z-index: 5; pointer-events: none; }
.dominance-hit { stroke: transparent; stroke-width: 12; fill: none; pointer-events: stroke; }
@media (prefers-reduced-motion: reduce) { .cost-marker { transition: none; } }
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
.dragging .column .tip, .dragging .column::before, .dragging .ring { display: none; }
.dragging .cost-point .tip { visibility: hidden; }
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
.zoom-head button { font: 28px/1 system-ui, sans-serif; color: var(--ink-2); background: none; border: 0; cursor: pointer;
  width: 44px; height: 44px; padding: 0; }
.zoom-legend { display: flex; flex-wrap: wrap; gap: 6px 18px; margin: 12px 0 4px; font-weight: 500; }
.zoom-legend span { display: inline-flex; align-items: center; gap: 8px; }
.zoom-legend span::before { content: ""; width: 18px; height: 3px; border-radius: 2px; background: var(--series); }
.zoom-plot { flex: 1; min-height: 0; position: relative; }
.zoom-plot svg { display: block; width: 100%; height: 100%; overflow: visible; }
$toggles
</style>
</head>
<body>
<header class="shell intro"><h1>$title</h1><p class="tagline">$tagline</p>
<p class="hint"><span class="effort-hint">Hold, then drag across a chart to zoom.</span>
<span class="cost-hint">Grey arrows point to a better deal.</span></p></header>
<nav class="controls" aria-label="Chart controls">$controls</nav>
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
<dialog id="benchmark-versions" aria-labelledby="version-heading">
<div class="version-dialog-head"><h3 id="version-heading">Older scores</h3>
<form method="dialog"><button aria-label="Close older scores">×</button></form></div>
<p>Different versions use different tasks or scoring.</p><div class="version-list"></div>
</dialog>
<script type="application/json" id="chart-data">$data</script>
<script>
$script
</script>
</body>
</html>
""")


CHECK_ICON = '<svg viewBox="0 0 12 12" aria-hidden="true"><path d="M2.5 6.2 4.8 8.5 9.5 3.8"/></svg>'
FILTER_ICON = ('<svg viewBox="0 0 20 20" aria-hidden="true"><path d="M3 6h8m4 0h2M3 14h2m4 0h8"/>'
               '<circle cx="13" cy="6" r="2"/><circle cx="7" cy="14" r="2"/></svg>')
CHEVRON_ICON = '<svg class="chevron" viewBox="0 0 20 20" aria-hidden="true"><path d="m5 8 5 5 5-5"/></svg>'


def chip_html(name: str, input_id: str, value: str, label: str, color: str) -> str:
    """A multi-select chip whose checkbox lives inside it, so CSS styles it from its own state.

    >>> chip_html("model", "show-a", "a", "A", "ink-2").count('checked')
    1
    """
    return (f'<label class="chip" for="{input_id}" style="--series: var(--{color})">'
            f'<input type="checkbox" class="toggle" name="{name}" id="{input_id}" value="{value}" '
            f'data-label="{html.escape(label)}" checked><span class="tick">{CHECK_ICON}</span>{html.escape(label)}</label>')


def filter_group_html(group: str, title: str, chips: str) -> str:
    return (f'<section class="filter-group {group}" aria-label="{title}"><div class="group-head">'
            f'<span class="group-title">{title}</span><span class="quick">'
            f'<button type="button" id="{group}-all" data-group="{group}" data-checked="true">All</button>'
            f'<button type="button" id="{group}-none" data-group="{group}" data-checked="false">None</button>'
            f'</span></div><div class="chips">{chips}</div></section>')


def controls_html() -> str:
    """The sticky bar: a filters disclosure and the x-axis switch, with the model and thinking-level chips below."""
    models = "".join(chip_html("model", f"show-{model.slug}", model.slug, model.name, model.color.variable)
                     for model in MODELS)
    levels = "".join(chip_html("thinking-level", f"level-{level}", level, level.replace("-", " "), "ink-2")
                     for level in FILTER_LEVELS)
    axes = "".join(f'<label for="x-{mode}"><input type="radio" class="toggle" name="x-axis" id="x-{mode}" value="{mode}"'
                   f'{" checked" if mode == "effort" else ""}>{label}</label>'
                   for mode, label in (("effort", "Thinking level"), ("cost", "Cost")))
    return ('<input type="checkbox" class="toggle" id="filters-open" aria-controls="filter-panel">'
            f'<div class="shell bar"><label class="filters-button" for="filters-open">{FILTER_ICON}Filters'
            f'<span class="filter-summary"></span><span class="filter-dot"></span>{CHEVRON_ICON}</label>'
            f'<div class="segmented" role="radiogroup" aria-label="X axis"><span class="segmented-caption">X axis</span>{axes}</div></div>'
            f'<div class="filter-panel" id="filter-panel"><div class="panel-inner shell">'
            f'{filter_group_html("models", "Models", models)}{filter_group_html("levels", "Thinking level", levels)}'
            '<label class="done" for="filters-open">Done</label></div></div>')


def page_html() -> str:
    sections = []
    for name, section_charts in SECTIONS:
        panels = "".join(panel_html(chart) if isinstance(chart, Metric) else bar_panel_html(chart) for chart in section_charts)
        sections.append(f'<section><h2>{html.escape(name)}</h2><div class="grid">{panels}</div>'
                        f'<p class="footnote">{html.escape(FOOTNOTES[name])}</p></section>')
    return PAGE_TEMPLATE.substitute(
        title=TITLE,
        tagline=html.escape(TAGLINE),
        colors=" ".join(f"--{color.variable}: {color.value};" for color in COLORS),
        toggles=toggle_css(),
        layouts=layout_css(),
        controls=controls_html(),
        sections="\n".join(sections),
        table=table_html(),
        data=json.dumps(chart_data(), ensure_ascii=False).replace("</", "<\\/"),
        script=(Path(__file__).parent / "zoom.js").read_text(),
    )


def chart_data() -> dict[str, object]:
    """The scores the zoom script redraws from, keyed by the same slugs the page uses."""
    return {
        "versions": [{"name": name, "versions": [
            {"label": version.label, "charts": [{"key": slugify(chart), "runner": runner}
                                                 for chart, runner in version.runners.items()]}
            for version in family]} for name, family in BENCHMARK_VERSIONS.items()],
        "levels": EFFORT_LEVELS,
        "layouts": [{"name": layout.name, "minViewport": layout.min_viewport} for layout in LAYOUTS],
        "markerRadius": MARKER_SIZE / 2,
        "endLabelGap": END_LABEL_MIN_GAP_POINTS,
        "models": [{"slug": model.slug, "name": model.name, "color": model.color.variable} for model in MODELS],
        "metrics": {slugify(metric.name): {
            "name": metric.name,
            "unit": metric.unit_and_source,
            "yRange": metric.y_range,
            "tickStep": metric.tick_step,
            "decimals": metric.decimals,
            "scores": {model.slug: metric.scores[model] for model in metric.models},
            "estimated": [[model.slug, EFFORT_LEVELS.index(level)] for model, level in metric.estimated],
            "costs": {model.slug: costs for model, costs in (metric.costs or {}).items()},
            "costUnit": metric.cost_unit,
        } for metric in [*CURVES, *(reported_cost_metric(reported) for reported in REPORTED if reported.costs)]},
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
        for category, metric in sectioned(ReportedMetric):
            for model, (score, effort) in metric.scores.items():
                writer.writerow([category.lower(), metric.name, metric.unit_and_source, model.name, "score",
                                 *(score if effort == level else "" for level in EFFORT_LEVELS), score, effort])
                if model in metric.prices:
                    writer.writerow([category.lower(), metric.name, metric.cost_unit, model.name, "cost_usd",
                                     *("" for _ in EFFORT_LEVELS), metric.prices[model], effort])
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
