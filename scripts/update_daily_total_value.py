#!/usr/bin/env python3
"""
Append new TSLA rows from daily_summary_multi.csv into data/daily_total_value_{mode}.csv.

Default target : data/daily_total_value_live.csv  (currently active mode)
Override       : --target data/daily_total_value_paper.csv

Filters source to strategy == "TSLA策略" and appends only dates not yet in the target.

Capital convention (overrides bot's bookkeeping)
------------------------------------------------
* STARTING_CAPITAL is the initial deposit, fixed at $2000.
* initial_value_t = STARTING_CAPITAL + sum(Injection_{≤t})  — grows ONLY with
  external DDI injections, NOT with profit-resets. (The bot's `initial_value`
  also includes locked-in profits, which inflates the principal artificially.)
* P/L_t          = total_value_t - initial_value_t       — true gain on capital at risk
* P/L_percent_t  = P/L_t / initial_value_t

Derived metrics
---------------
  daily_return  : (total_value_t - Injection_t - total_value_{t-1}) / total_value_{t-1}
                  Time-weighted: capital added isn't counted as return.
  Injection     : daily $ injection — change in source's ddi_total_injected.
  MaxDrawDown   : source drawdown_pct / 100   (bot's running portfolio_peak ref)
  SharpeRatio   : annualized; empty until cumulative sample ≥ MIN_DAYS_FOR_SHARPE (=20).
"""
from __future__ import annotations

import argparse
import csv
import math
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DST = ROOT / "data" / "daily_total_value_live.csv"

STRATEGY = "TSLA策略"
STARTING_CAPITAL = 2000.00

TARGET_HEADER = [
    "strategy", "date", "total_value", "daily_return",
    "initial_value", "Injection", "P/L", "P/L_percent",
    "MaxDrawDown", "SharpeRatio",
]

RF_ANNUAL = 0.0368
TRADING_DAYS = 252
MIN_DAYS_FOR_SHARPE = 20
RF_DAILY = (1 + RF_ANNUAL) ** (1 / TRADING_DAYS) - 1


def compute_sharpe(returns):
    n = len(returns)
    if n < MIN_DAYS_FOR_SHARPE:
        return ""
    excess = [r - RF_DAILY for r in returns]
    mean = sum(excess) / n
    var = sum((x - mean) ** 2 for x in excess) / (n - 1)
    std = math.sqrt(var)
    if std == 0:
        return ""
    return f"{(mean / std) * math.sqrt(TRADING_DAYS):.4f}"


def find_default_source():
    for c in (ROOT.parent / "daily_summary_multi.csv",
              ROOT.parent / "alpaca" / "daily_summary_multi.csv"):
        if c.exists():
            return c
    return None


def parse_args():
    p = argparse.ArgumentParser(description="Append TSLA rows to daily_total_value_{paper,live}.csv")
    p.add_argument("--source", type=Path, default=None,
                   help="Path to daily_summary_multi.csv (auto-detected if omitted)")
    p.add_argument("--target", type=Path, default=DEFAULT_DST,
                   help=f"Target CSV (default: {DEFAULT_DST.name})")
    return p.parse_args()


def read_source(path):
    if not path.exists():
        sys.exit(f"ERROR: source not found: {path}")
    with open(path, newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    if not rows:
        sys.exit(f"ERROR: source is empty: {path}")
    needed = {"date", "strategy", "total_value", "drawdown_pct", "ddi_total_injected"}
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
    prev_ddi_cum = sum(fnum(r.get("Injection", 0)) for r in dst_rows)
    all_returns = [fnum(r["daily_return"]) for r in dst_rows]

    src_rows.sort(key=lambda r: r["date"])
    new_rows = []
    for r in src_rows:
        if r["date"] in existing_dates:
            continue
        total_value = fnum(r["total_value"])
        if total_value == 0:
            # skip bot startup / placeholder rows where positions weren't opened
            continue
        curr_ddi_cum = fnum(r["ddi_total_injected"])
        daily_injection = curr_ddi_cum - prev_ddi_cum

        if prev_total is None or prev_total == 0:
            daily_return = 0.0
        else:
            daily_return = (total_value - daily_injection - prev_total) / prev_total
        all_returns.append(daily_return)

        # Override bot's initial_value with our anchored version
        initial_value = STARTING_CAPITAL + curr_ddi_cum
        pl = total_value - initial_value
        pl_pct = pl / initial_value if initial_value else 0.0

        out = {
            "strategy":      STRATEGY,
            "date":          r["date"],
            "total_value":   f"{total_value:.6f}",
            "daily_return":  f"{daily_return:.6f}",
            "initial_value": f"{initial_value:.2f}",
            "Injection":     f"{daily_injection:.4f}",
            "P/L":           f"{pl:.6f}",
            "P/L_percent":   f"{pl_pct:.6f}",
            "MaxDrawDown":   f"{fnum(r['drawdown_pct']) / 100.0:.6f}",
            "SharpeRatio":   compute_sharpe(all_returns),
        }
        new_rows.append(out)
        prev_total = total_value
        prev_ddi_cum = curr_ddi_cum
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

    print(f"APPENDED {len(new_rows)} rows for {STRATEGY} → {dst_path.name}:")
    for r in new_rows:
        sharpe_str = r["SharpeRatio"] if r["SharpeRatio"] else "—"
        inj_str = f"+${r['Injection']}" if float(r["Injection"]) > 0 else "—"
        print(f"  {r['date']}  total={r['total_value']}  init={r['initial_value']}  inj={inj_str}  P/L={r['P/L']}  Sharpe={sharpe_str}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
