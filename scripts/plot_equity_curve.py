#!/usr/bin/env python3
"""Generate equity curve PNG from a daily_total_value_*.csv file.

Default source: data/daily_total_value_paper.csv
Switch to live: --source data/daily_total_value_live.csv

Handles 0 rows (skips) and 1 row (single-point chart).
"""
import argparse
import csv
import sys
from datetime import datetime
from pathlib import Path
import matplotlib.pyplot as plt
import matplotlib.dates as mdates

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SRC = ROOT / "data" / "daily_total_value_paper.csv"
DEFAULT_OUT = ROOT / "charts" / "tsla_equity.png"


def load(path):
    rows = []
    with open(path) as f:
        for r in csv.DictReader(f):
            rows.append({
                "date": datetime.strptime(r["date"], "%Y-%m-%d"),
                "total_value": float(r["total_value"]),
                "initial_value": float(r["initial_value"]),
                "pl": float(r["P/L"]),
                "pl_pct": float(r["P/L_percent"]),
            })
    return rows


def plot(rows, out_path, src_name):
    dates = [r["date"] for r in rows]
    values = [r["total_value"] for r in rows]
    initial = rows[0]["initial_value"]
    final = values[-1]
    final_pl = rows[-1]["pl"]
    final_pl_pct = rows[-1]["pl_pct"] * 100
    peak = max(values)

    fig, ax = plt.subplots(figsize=(11, 5.5), dpi=130)
    line_color = "#2f7ed8" if final >= initial else "#d04848"
    ax.plot(dates, values, color=line_color, linewidth=2.2, marker="o",
            markersize=4, markerfacecolor="white",
            markeredgecolor=line_color, label="Total Value")

    ax.axhline(initial, color="#7a7a7a", linestyle="--", linewidth=1,
               alpha=0.7, label=f"Initial ${initial:,.0f}")

    if len(rows) > 1:
        ax.fill_between(dates, values, initial,
                        where=[v >= initial for v in values],
                        color="#2f7ed8", alpha=0.10, interpolate=True)
        ax.fill_between(dates, values, initial,
                        where=[v < initial for v in values],
                        color="#d04848", alpha=0.10, interpolate=True)

    ax.annotate(f"Start\n${values[0]:,.0f}", xy=(dates[0], values[0]),
                xytext=(8, 14), textcoords="offset points",
                fontsize=9, color="#444",
                arrowprops=dict(arrowstyle="-", color="#aaa", lw=0.8))

    pl_sign = "+" if final_pl >= 0 else ""
    ax.annotate(f"End ${final:,.2f}\nP/L {pl_sign}${final_pl:,.2f} ({pl_sign}{final_pl_pct:.2f}%)",
                xy=(dates[-1], final),
                xytext=(-110, -38 if final < initial else 18),
                textcoords="offset points",
                fontsize=9.5, color=line_color, fontweight="bold",
                arrowprops=dict(arrowstyle="->", color=line_color, lw=1))

    if peak > initial and dates[values.index(peak)] not in (dates[0], dates[-1]):
        pi = values.index(peak)
        ax.annotate(f"Peak ${peak:,.2f}",
                    xy=(dates[pi], peak),
                    xytext=(0, 12), textcoords="offset points",
                    fontsize=8.5, color="#2c8a3a", ha="center",
                    arrowprops=dict(arrowstyle="-", color="#88c294", lw=0.8))

    ax.set_title("Daily Total Value", fontsize=14, fontweight="bold", pad=14)
    ax.set_xlabel("Date", fontsize=10)
    ax.set_ylabel("Total Value (USD)", fontsize=10)
    ax.grid(True, linestyle=":", alpha=0.45)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)

    ax.xaxis.set_major_locator(mdates.AutoDateLocator(maxticks=10))
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%m-%d"))
    fig.autofmt_xdate(rotation=0, ha="center")
    ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, _: f"${x:,.0f}"))
    ax.legend(loc="lower left", frameon=False, fontsize=9)

    fig.text(0.99, 0.01,
             f"Source: {src_name}  ·  Updated {rows[-1]['date']:%Y-%m-%d}",
             ha="right", va="bottom", fontsize=8, color="#888")

    fig.tight_layout()
    out_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out_path, dpi=130, bbox_inches="tight")
    print(f"Saved {out_path}  ({len(rows)} points, final ${final:,.2f}, P/L {pl_sign}${final_pl:,.2f})")


def parse_args():
    p = argparse.ArgumentParser(description="Plot daily total value equity curve")
    p.add_argument("--source", type=Path, default=DEFAULT_SRC,
                   help=f"CSV file to plot (default: {DEFAULT_SRC.name})")
    p.add_argument("--output", type=Path, default=DEFAULT_OUT,
                   help=f"Output PNG path (default: {DEFAULT_OUT.name})")
    return p.parse_args()


if __name__ == "__main__":
    args = parse_args()
    if not args.source.exists():
        print(f"Source not found: {args.source} — skipping.")
        sys.exit(0)
    rows = load(args.source)
    if not rows:
        print(f"No data rows in {args.source} — skipping chart regeneration.")
        sys.exit(0)
    rows.sort(key=lambda r: r["date"])
    plot(rows, args.output, args.source.name)
