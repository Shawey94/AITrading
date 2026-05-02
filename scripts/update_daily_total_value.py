#!/usr/bin/env python3
"""
Append new TSLA rows from daily_summary_multi.csv into data/daily_total_value.csv.

Source : ../daily_summary_multi.csv  (trading bot output, one row per strategy per day)
Target : data/daily_total_value.csv  (curated TSLA-only history with derived metrics)

Behaviour
---------
* Filters source to strategy == "TSLA策略".
* For each TSLA date NOT already in the target, appends a new row with:
    strategy       <- "TSLA策略"
    date           <- date
    total_value    <- total_value
    daily_return   <- (total_value - prev_total_value) / prev_total_value
                      ('prev' = the most recent row in target, or 0 on first ever row)
    initial_value  <- initial_value
    P/L            <- pl_amount
    P/L_percent    <- pl_percent / 100         (source stores as %, target stores as fraction)
    MaxDrawDown    <- drawdown_pct / 100       (uses bot's running portfolio_peak as reference;
                                                NOTE: differs from README formula which uses
                                                rolling max of total_value. See README caveat.)
    SharpeRatio    <- ""                       (blank: not yet implemented)

Idempotent: re-running on the same day adds nothing.

Exit codes
----------
0  rows appended, OR nothing-to-do
1  source missing/malformed, or other unrecoverable error
"""
from __future__ import annotations

import argparse
import csv
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DST = ROOT / "data" / "daily_total_value.csv"

STRATEGY = "TSLA策略"
TARGET_HEADER = [
    "strategy", "date", "total_value", "daily_return",
    "initial_value", "P/L", "P/L_percent", "MaxDrawDown", "SharpeRatio",
]


def find_default_source():
    """Look for daily_summary_multi.csv in several plausible locations."""
    candidates = [
        # Windows / native: parent of repo (C:\...\alpaca\)
        ROOT.parent / "daily_summary_multi.csv",
        # Linux sandbox where AITrading and alpaca are sibling mounts
        ROOT.parent / "alpaca" / "daily_summary_multi.csv",
    ]
    for c in candidates:
        if c.exists():
            return c
    return None


def parse_args():
    p = argparse.ArgumentParser(description="Append TSLA rows to daily_total_value.csv")
    p.add_argument("--source", type=Path, default=None,
                   help="Path to daily_summary_multi.csv (auto-detected if omitted)")
    p.add_argument("--target", type=Path, default=DEFAULT_DST,
                   help="Path to daily_total_value.csv inside the repo")
    return p.parse_args()


def read_source(path):
    if not path.exists():
        sys.exit(f"ERROR: source not found: {path}")
    with open(path, newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    if not rows:
        sys.exit(f"ERROR: source is empty: {path}")
    needed = {"date", "strategy", "total_value", "initial_value",
              "pl_amount", "pl_percent", "drawdown_pct"}
    missing = needed - set(rows[0].keys())
    if missing:
        sys.exit(f"ERROR: source missing columns: {sorted(missing)}")
    return [r for r in rows if r["strategy"] == STRATEGY]


def read_target(path):
    if not path.exists():
        return TARGET_HEADER, []
    with open(path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        return reader.fieldnames or TARGET_HEADER, list(reader)


def fnum(s):
    return float(s) if s not in ("", None) else 0.0


def transform(src_row, prev_total):
    total_value = fnum(src_row["total_value"])
    if prev_total is None or prev_total == 0:
        daily_return = 0.0
    else:
        daily_return = (total_value - prev_total) / prev_total
    return {
        "strategy":      STRATEGY,
        "date":          src_row["date"],
        "total_value":   f"{total_value:.6f}",
        "daily_return":  f"{daily_return:.6f}",
        "initial_value": f"{fnum(src_row['initial_value']):.2f}",
        "P/L":           f"{fnum(src_row['pl_amount']):.6f}",
        "P/L_percent":   f"{fnum(src_row['pl_percent']) / 100.0:.6f}",
        "MaxDrawDown":   f"{fnum(src_row['drawdown_pct']) / 100.0:.6f}",
        "SharpeRatio":   "",
    }


def main():
    args = parse_args()
    src_path = args.source or find_default_source()
    if src_path is None:
        sys.exit("ERROR: could not locate daily_summary_multi.csv. Pass --source explicitly.")
    dst_path = args.target

    src_rows = read_source(src_path)
    if not src_rows:
        print(f"NO_SOURCE_ROWS for strategy={STRATEGY}")
        return 0

    header, dst_rows = read_target(dst_path)
    existing_dates = {r["date"] for r in dst_rows}
    prev_total = fnum(dst_rows[-1]["total_value"]) if dst_rows else None

    src_rows.sort(key=lambda r: r["date"])
    new_rows = []
    for r in src_rows:
        if r["date"] in existing_dates:
            continue
        out = transform(r, prev_total)
        new_rows.append(out)
        prev_total = float(out["total_value"])
        existing_dates.add(r["date"])

    if not new_rows:
        print("NO_NEW_ROWS")
        return 0

    dst_path.parent.mkdir(parents=True, exist_ok=True)
    with open(dst_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=TARGET_HEADER)
        writer.writeheader()
        for r in dst_rows:
            writer.writerow({k: r.get(k, "") for k in TARGET_HEADER})
        for r in new_rows:
            writer.writerow(r)

    print(f"APPENDED {len(new_rows)} rows for {STRATEGY}:")
    for r in new_rows:
        print(f"  {r['date']}  total={r['total_value']}  P/L={r['P/L']}  MDD={r['MaxDrawDown']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
