#!/usr/bin/env python3
"""Three-panel teaser template for papers.

Panel (a): motivation, schematic illustration.
Panel (b): analysis, data-driven plot from CSV.
Panel (c): result, comparison consistent with paper numbers.

Style follows paper conventions: PDF output, small fonts, single-column
width, no top/right spines, subtle grid.

Usage:  python teaser_template.py
"""

import csv
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

OUT = "teaser_overview.pdf"
CSV = "figures/convergence.csv"  # replace with your data source

plt.rcParams.update({
    "axes.linewidth": 0.6,
    "xtick.direction": "out",
    "ytick.direction": "out",
    "xtick.major.size": 2.5,
    "ytick.major.size": 2.5,
    "grid.linewidth": 0.4,
    "font.size": 7,
})


def style_ax(ax):
    for spine in ("top", "right"):
        ax.spines[spine].set_visible(False)
    ax.grid(axis="y", color="0.88", zorder=0)
    ax.set_axisbelow(True)


def draw_motivation(ax):
    """Schematic: predictions colored by coverage."""
    rng = np.random.default_rng(0)
    points = rng.uniform(0, 1, (60, 2))
    covered = points[:, 0] < 0.3
    colors = ["0.35" if flag else (0.78, 0.13, 0.13) for flag in covered]
    ax.scatter(points[:, 0], points[:, 1], s=8, c=colors, zorder=3)
    ax.set_xlim(-0.05, 1.05)
    ax.set_ylim(-0.05, 1.05)
    ax.set_aspect("equal")
    ax.set_xticks([])
    ax.set_yticks([])
    style_ax(ax)
    ax.set_title("(a) motivation", fontsize=7)


def draw_analysis(ax):
    """Data-driven plot. Numbers must match the paper."""
    data = []
    if Path(CSV).exists():
        with open(CSV, encoding="utf-8") as handle:
            for row in csv.reader(handle):
                if not row or row[0].startswith("#") or row[0] == "u":
                    continue
                data.append((int(row[0]), float(row[2])))
    if data:
        xs = [item[0] for item in data]
        ys = [item[1] for item in data]
    else:
        xs = [1, 2, 3, 6]
        ys = [0.30, 0.27, 0.25, 0.22]
    ax.plot(xs, ys, marker="o", ms=3, lw=1.1, color=(0.16, 0.42, 0.66))
    ax.set_xlabel("x label", fontsize=6.5)
    ax.set_ylabel("y label", fontsize=6.5)
    ax.tick_params(labelsize=5.5)
    style_ax(ax)
    ax.set_title("(b) analysis", fontsize=7)


def draw_result(ax):
    """Result comparison. Values must match the paper numbers."""
    methods = ["Baseline", "Ours"]
    values = [0.149, 0.148]
    ax.bar(methods, values, width=0.55, color=["0.55", (0.78, 0.13, 0.13)])
    for index, value in enumerate(values):
        ax.text(index, value + 0.001, f"{value:.3f}", ha="center", fontsize=5.5)
    ax.set_ylabel("metric", fontsize=6.5)
    ax.set_ylim(0, max(values) * 1.2)
    ax.tick_params(labelsize=5.5)
    style_ax(ax)
    ax.set_title("(c) result", fontsize=7)


fig, axes = plt.subplots(1, 3, figsize=(3.3, 1.28))
plt.subplots_adjust(wspace=0.4)
draw_motivation(axes[0])
draw_analysis(axes[1])
draw_result(axes[2])
fig.savefig(OUT, bbox_inches="tight", pad_inches=0.02)
print("wrote", OUT)
