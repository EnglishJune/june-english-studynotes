#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path

import matplotlib.pyplot as plt

LEVELS = ["A1", "A2", "B1", "B2", "C1", "C2"]
BAR_COLORS = ["#dfe7c2", "#d3dfb5", "#b9cfae", "#9ebcab", "#7ea394", "#5c8878"]
TEXT_COLOR = "#24322b"
BASELINE_COLOR = "#83a78d"


def percentage(value, level):
    if isinstance(value, dict):
        value = value.get("percentage")
    try:
        out = float(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{level} percentage must be numeric") from exc
    if not 0 <= out <= 100:
        raise ValueError(f"{level} percentage must be between 0 and 100")
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("statistics_json")
    ap.add_argument("output_png")
    a = ap.parse_args()

    d = json.loads(Path(a.statistics_json).read_text(encoding="utf-8"))
    levels = d.get("levels")
    if not isinstance(levels, dict):
        raise ValueError("CEFR statistics must contain a levels object")
    missing = [level for level in LEVELS if level not in levels]
    if missing:
        raise ValueError("CEFR statistics missing levels: " + ", ".join(missing))
    vals = [percentage(levels[level], level) for level in LEVELS]
    if abs(sum(vals) - 100) > 0.5:
        raise ValueError("CEFR percentages must sum to approximately 100")

    fig, ax = plt.subplots(figsize=(7.2, 3.05), dpi=220)
    fig.patch.set_alpha(0)
    ax.set_facecolor("none")

    bars = ax.bar(LEVELS, vals, width=0.62, color=BAR_COLORS, edgecolor="none")
    top = max(vals) if vals else 0
    label_offset = max(0.6, top * 0.035)
    for bar, value in zip(bars, vals):
        ax.text(
            bar.get_x() + bar.get_width() / 2,
            value + label_offset,
            f"{value:.1f}%",
            ha="center",
            va="bottom",
            fontsize=10.5,
            color=TEXT_COLOR,
            fontweight="bold",
        )

    ax.set_ylim(0, max(5, top * 1.16))
    ax.yaxis.set_visible(False)
    ax.grid(False)
    for spine in ["left", "right", "top"]:
        ax.spines[spine].set_visible(False)
    ax.spines["bottom"].set_visible(True)
    ax.spines["bottom"].set_color(BASELINE_COLOR)
    ax.spines["bottom"].set_linewidth(1.0)
    ax.tick_params(axis="x", length=0, pad=7, colors=TEXT_COLOR, labelsize=10.5)
    for label in ax.get_xticklabels():
        label.set_fontweight("bold")

    fig.subplots_adjust(left=0.02, right=0.995, top=0.95, bottom=0.16)
    fig.savefig(a.output_png, transparent=True, bbox_inches="tight", pad_inches=0.03)
    plt.close(fig)
    print(a.output_png)


if __name__ == "__main__":
    main()
